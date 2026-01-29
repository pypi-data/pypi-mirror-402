"""This module contains the implementation of CodeGrade's pytest reporter plugin
for use in AutoTest v2.

The plugin is automatically enabled, but can be disabled by running pytest with
the following command line flags:

    pytest -p no:cg-pytest-reporter
"""

import dataclasses
import json
import logging
import os
import subprocess
import typing as t
from fractions import Fraction

import _pytest.nodes
import pytest
from _pytest.junitxml import mangle_test_address

logger = logging.getLogger('cg_pytest_reporter')


def _json_default(obj: object) -> object:
    """The default method to use objects that we naively cannot marshal."""
    # Currently we only add support for fractions.
    if isinstance(obj, Fraction):
        return str(obj)
    raise TypeError  # pragma: no cover


def json_dumps(obj: object) -> str:
    """Dump an object to JSON without any extra formatting."""
    # Make sure only ASCII characters are used so that the string length as
    # python's `len` function reports it is equal to the string's byte length.
    # Do not insert spaces after each separator.
    return (
        json.dumps(
            obj,
            ensure_ascii=True,
            separators=(',', ':'),
            default=_json_default,
        )
        + '\n'
    )


class MessageTooLargeException(Exception):
    """This exception is raised when the required fields of the message combined
    are too large.
    """


PyTestCaseStatus = t.Literal['passed', 'failed', 'skipped']
CgTestCaseStatus = t.Literal['success', 'failure', 'skipped']

# Mapping from the status used by pytest to the status used by CodeGrade.
STATUS_NAME_MAP: t.Mapping[PyTestCaseStatus, CgTestCaseStatus] = {
    'passed': 'success',
    'failed': 'failure',
    'skipped': 'skipped',
}


class _TestCaseResultReq(t.TypedDict):
    """The required properties of a test case result."""

    #: The name of the test case.
    name: str
    #: The result of the test case.
    status: CgTestCaseStatus


class TestCaseResult(_TestCaseResultReq, total=False):
    """The optional properties of a test case result."""

    #: The description of the test case.
    description: str
    #: The weight of the test case.
    weight: Fraction
    #: The reason the test case failed or was skipped.
    reason: str
    #: The stdout produced by the test case.
    stdout: str
    #: The stderr produced by the test case.
    stderr: str


class _TestSuiteResultReq(t.TypedDict):
    """The required properties of a test suite result."""

    #: The id of this suite. Test cases within the same file
    #: are in the same suite.
    id: str
    #: The file name of the test that was run.
    name: str
    #: The results of the test cases in this suite.
    testCases: t.List[TestCaseResult]


class TestSuiteResult(_TestSuiteResultReq, total=False):
    """The optional properties of a test suite result."""

    #: The weight of the test suite.
    weight: Fraction


class UnitTestMessage(t.TypedDict):
    """The message to be sent for each test case."""

    #: Message tag.
    tag: t.Literal['unit-test']
    #: The test results.
    results: t.List[TestSuiteResult]


@dataclasses.dataclass
class CGMarks:
    """Marks set on each test case by the `cg-pytest-reporter` plugin used when
    generating the report.
    """

    #: The name of the test suite.
    suite_name: t.Optional[str]
    #: The weight of the test suite.
    suite_weight: t.Optional[Fraction]

    #: The name of the test case.
    name: t.Optional[str]
    #: The description of the test case.
    description: t.Optional[str]
    #: The weight of the test case.
    weight: t.Optional[Fraction]
    #: The reason the test failed.
    reason: t.Optional[str]
    #: The stdout produced while running the test.
    hide_stdout: bool
    #: The stderr produced while running the test.
    hide_stderr: bool

    @classmethod
    def from_item(cls, item: pytest.Item) -> 'CGMarks':
        """Get the CodeGrade marks from the given item.

        :param item: The item to get the marks from.
        :returns: A new `CGMarks` instance.
        """
        return CGMarks(
            suite_name=cls._as_str(
                cls._get_suite_mark_value(item, 'cg_suite_name')
            ),
            suite_weight=cls._as_num(
                cls._get_suite_mark_value(item, 'cg_suite_weight')
            ),
            name=cls._as_str(cls._get_mark_value(item, 'cg_name')),
            description=cls._as_str(
                cls._get_mark_value(item, 'cg_description')
            ),
            weight=cls._as_num(cls._get_mark_value(item, 'cg_weight')),
            reason=cls._as_str(cls._get_mark_value(item, 'cg_reason')),
            hide_stdout=item.get_closest_marker('cg_hide_stdout') is not None,
            hide_stderr=item.get_closest_marker('cg_hide_stderr') is not None,
        )

    @classmethod
    def _get_suite_mark_value(
        cls,
        item: pytest.Item,
        name: str,
    ) -> t.Optional[object]:
        parent = item.parent
        # It is not possible to add marks on the module level because you cannot
        # call a decorator on a module. So on the module level we allow a custom
        # name and weight by setting the `__cg_suite_{name,weight}__` variables
        # at the top level of the module.
        if parent is None:
            # An `Item` always has a parent, which is either the module or test
            # class.
            return None  # pragma: no cover
        elif isinstance(parent, pytest.Module):
            # Pytest offers no way to get the module object from a `Module` node.
            return getattr(parent._obj, f'__{name}__', None)
        else:
            return cls._get_mark_value(parent, name)

    @classmethod
    def _get_mark_value(
        cls,
        item: _pytest.nodes.Node,
        name: str,
    ) -> t.Optional[object]:
        mark: t.Optional[pytest.Mark] = item.get_closest_marker(name)
        if mark is None or not mark.args:
            return None
        return mark.args[0]

    @staticmethod
    def _as_str(obj: object) -> t.Optional[str]:
        if isinstance(obj, str):
            return obj
        return None

    @staticmethod
    def _as_num(obj: object) -> t.Optional[Fraction]:
        if isinstance(obj, Fraction):
            return obj
        elif isinstance(obj, str):
            try:
                return Fraction(obj)
            except ValueError:
                return None
        elif isinstance(obj, int):
            return Fraction(obj)
        elif isinstance(obj, float):
            return Fraction(obj).limit_denominator(100)
        return None


class CGPytestReporterPlugin:
    """Implementation of the reporter plugin.

    This creates a new subprocess to run `cg truncate`, and writes all messages
    to its input. The `cg truncate` command is then responsible for merging
    and truncating messages to the maximum size.

    This intercepts the `pytest_runtest_makereport` hook to get all the marks
    that were set on a test item, which is necessary because the value of those
    marks is no longer retrievable in the `pytest_runtest_logreport` call.

    This also has a `pytest_runtest_logreport` hook that will actually write the
    report to `cg truncate`.
    """

    _config: pytest.Config
    _file: t.IO[bytes]
    _proc: t.Union[subprocess.Popen, None] = None

    _points_achieved: Fraction = Fraction(0, 1)
    _points_possible: Fraction = Fraction(0, 1)

    def __init__(self, config: pytest.Config) -> None:
        self._config = config

        # We need access to the resources after this function has ended.
        if self._should_truncate():
            self._proc = subprocess.Popen(
                ['cg', 'truncate'],
                # The `cg` command already does buffering for us, so disable
                # buffering.
                bufsize=0,
                stdin=subprocess.PIPE,
                close_fds=False,
            )
            assert self._proc.stdin is not None
            self._file = self._proc.stdin
        else:
            self._file = open(2, 'wb', buffering=0)

    def deinit(self) -> None:
        """Deinitialize the plugin.

        This cleans up opened files and subprocesses.
        """
        # When running in ATv2, this will close the stdin of the `cg truncate`
        # command, which will cause it to flush its buffers and terminate.
        self._file.close()
        if self._proc is not None:
            self._proc.wait()

    @staticmethod
    def _should_truncate() -> bool:
        """Whether to truncate the output with the `cg truncate` command."""
        if os.environ.get('CG_ATV2') == 'true':
            return True
        if os.environ.get('CG_PYTEST_REPORTER_TRUNCATE') == 'true':
            return True
        return False

    @staticmethod
    def pytest_runtest_makereport(
        item: pytest.Item,
        call: pytest.CallInfo[None],
    ) -> pytest.TestReport:
        """Create the report for logging.

        This hook must return a `pytest.TestReport`, but that class is marked
        `@final` so we are not allowed to subclass it.

        :param item: The item to generate a report for.
        :param call: The result of the test function invocation.
        :returns: A report for the test that was run, including an extra
            `_cg_marks` attribute to make it possible to retrieve the mark
            values in the `pytest_runtest_logreport` hook.
        """
        report = pytest.TestReport.from_item_and_call(item, call)
        # `TestReport` has no property `_cg_marks`...
        report._cg_marks = CGMarks.from_item(item)  # type: ignore
        return report

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        """Write the report to the given file descriptor.

        :param report: The report to write.
        :returns: Nothing.
        """
        # This hook is called multiple times for each test. For tests that are
        # not skipped the report contains the information we need during the
        # "call" phase.
        if report.when == 'call':
            self._send_message(report)

        # Because a skipped test is never ran, we never get a message for it
        # during the "call" phase but we do get a message for it during the
        # "setup" phase.
        if report.when == 'setup' and report.outcome == 'skipped':
            self._send_message(report)

    def _send_message(self, report: pytest.TestReport) -> None:
        message: UnitTestMessage = {
            'tag': 'unit-test',
            'results': [self._mk_test_suite(report)],
        }

        data = json_dumps(message)

        self._file.write(data.encode('utf8'))

        self._update_score(report)

    def _mk_test_suite(self, report: pytest.TestReport) -> TestSuiteResult:
        *suite_name_parts, case_name = mangle_test_address(report.nodeid)
        suite_name = '.'.join(suite_name_parts)

        test_suite: TestSuiteResult = {
            'id': suite_name,
            'name': suite_name,
            'testCases': [self._mk_test_case(case_name, report)],
        }

        marks = t.cast(CGMarks, report._cg_marks)

        if marks.suite_name is not None:
            test_suite['id'] = test_suite['name'] = marks.suite_name
        if marks.suite_weight is not None:
            test_suite['weight'] = marks.suite_weight

        return test_suite

    @staticmethod
    def _mk_test_case(name: str, report: pytest.TestReport) -> TestCaseResult:
        status = STATUS_NAME_MAP[report.outcome]

        test_case: TestCaseResult = {
            'name': name,
            'status': status,
        }

        marks = t.cast(CGMarks, report._cg_marks)

        if marks.name is not None:
            test_case['name'] = marks.name
        if marks.description is not None:
            test_case['description'] = marks.description
        if marks.weight is not None:
            test_case['weight'] = marks.weight

        if marks.reason is not None:
            test_case['reason'] = marks.reason
        elif report.longrepr is None:
            pass
        else:
            longrepr = report.longrepr
            # Long repr is an annoyingly big `t.Union`...
            if isinstance(longrepr, tuple):
                # If it is a tuple it has 3 elements: a path, a line number, and
                # the actual reason.
                reason = longrepr[2]
            else:
                reason = report.longreprtext
            test_case['reason'] = reason

        if report.capstdout and not marks.hide_stdout:
            test_case['stdout'] = report.capstdout
        if report.capstderr and not marks.hide_stderr:
            test_case['stderr'] = report.capstderr

        return test_case

    def _update_score(self, report: pytest.TestReport) -> None:
        if report.outcome == 'skipped':
            return

        marks = t.cast(CGMarks, report._cg_marks)
        weight = Fraction(1, 1)

        if marks.weight is not None:
            weight *= marks.weight
        if marks.suite_weight is not None:
            weight *= marks.suite_weight

        self._points_possible += weight
        if report.outcome == 'passed':
            self._points_achieved += weight

    def pytest_terminal_summary(self, *_: t.Any) -> None:
        """Write the final achieved score to the structured output.

        This uses the same format as the Custom Test step.
        """
        if self._points_possible == 0:
            points = Fraction(0)
        else:
            points = self._points_achieved / self._points_possible

        message = json_dumps({
            'tag': 'points',
            'points': points,
        })

        self._file.write(message.encode('utf8'))


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the --cg-pytest-fd command line option.

    This flag is deprecated, but cannot be removed for backwards compatibility
    reasons.
    """
    group = parser.getgroup('terminal reporting', 'report-log plugin options')
    group.addoption(
        '--cg-pytest-fd',
        type=int,
        action='store',
        metavar='file descriptor',
        default=1,
        help='File descriptor to write the results to.',
    )


def pytest_configure(config: pytest.Config) -> None:
    """Initialize the plugin.

    1. Register the plugin with Pytest's plugin manager.
    2. Configure the markers that are used by the plugin to prevent warnings
       being printed for them.
    """
    plugin = CGPytestReporterPlugin(config)
    config.pluginmanager.register(plugin, name='cg-pytest-reporter')

    config.addinivalue_line(
        'markers', 'cg_suite_name(str): Name of a test suite'
    )
    config.addinivalue_line(
        'markers',
        'cg_suite_weight(float | str | Fraction): Weight of a test suite',
    )

    config.addinivalue_line('markers', 'cg_name(str): Name of a test case')
    config.addinivalue_line(
        'markers', 'cg_description(str): Description of a test case'
    )
    config.addinivalue_line(
        'markers',
        'cg_weight(float | str | Fraction): Weight of a test case',
    )
    config.addinivalue_line(
        'markers', 'cg_reason(str): The reason a test case failed'
    )
    config.addinivalue_line(
        'markers',
        'cg_hide_stdout: Hide the stdout written while running this test',
    )
    config.addinivalue_line(
        'markers',
        'cg_hide_stderr: Hide the stderr written while running this test',
    )


def pytest_unconfigure(config: pytest.Config) -> None:
    """Deregister the plugin."""
    plugin = config.pluginmanager.unregister(name='cg-pytest-reporter')
    if isinstance(plugin, CGPytestReporterPlugin):
        plugin.deinit()
