# cg-pytest-reporter

A Pytest reporter plugin for CodeGrade AutoTest v2.

This plugin writes messages to CodeGrade AutoTest v2's structured output channel.
For each test that was run a `unit-test` message is written as described in
CodeGrade's documentation. When all tests have finished running, a final message
is written with the amount of points that were achieved in the test run.

## Utility functions

This plugin comes with a few utility functions to easily modify certain aspects
of each test case or test suite. All of these are decorators that you can apply
directly to your test functions or classes.

### Test suite decorators

These decorators change properties of an entire test suite. In terms of Pytest
that is a single file containing test functions, or a single class within such a
file.

#### `suite_name`

With the `suite_name` you can modify the name of a test suite that will be
displayed in the AutoTest v2 UI.

```python
from cg_pytest_reporter import suite_name


@suite_name('My Test Suite')
class TestSuite:
    def test_function():
        assert True
```

Because it is not possible to decorate an entire module, it is possible to
change the name of the module-level suite by setting the `__cg_suite_name__`
variable on the module.

```python
__cg_suite_name__ = 'My Test Suite'


def test_function():
    assert True
```

#### `suite_weight`

Use the `suite_weight` decorator to change the weight of an entire suite
relative to other suites in your test run.

You can use strings, integers, floats and fractions.Fraction as
weight. For the best precision strings, integers and fractions are
recommended.

```python
from cg_pytest_reporter import suite_weight


@suite_weight('2.1')
class TestSuite:
    def test_function():
        assert True
```

Similar to the suite name, you can set the weight of the module-level suite with
the `__cg_suite_weight__` variable.

```python
import fractions

__cg_suite_weight__ = fractions.Fraction(2, 1)
# Or:
# __cg_suite_weight__ = 2


def test_function():
    assert True
```

### Test function decorators

These decorators modify the behaviour of a single test case.

Although they work on the test case level, they can be applied to a class
containing test functions. This works as if the decorator was applied to each
test function individually, but each decorator can still be overridden on
individual test cases. It is mentioned on each of the decorators where this
might be useful.

#### `name`

With the `name` decorator you can change the name of a single test case.

```python
from cg_pytest_reporter import name


@name('My Cool Test')
def test_function():
    assert True
```

#### `description`

With the `description` decorator you can set a description for a single test
case. This can be useful if the name of the test function is not descriptive
enough.

```python
from cg_pytest_reporter import description


@description('A somewhat longer description of what is being tested.')
def test_function():
    assert True
```

#### `weight`

Change the weight of a single test function relative to other test functions
within the same suite.

You can use strings, integers, floats and fractions.Fraction as
weight. For the best precision strings, integers and fractions are
recommended.

```python
from cg_pytest_reporter import weight


@weight(2)
def test_function():
    assert True
```

This decorator can also be applied to a test class, in which case it will set a
default weight for all tests within that class which can still be overridden for
individual tests within that class. This can be useful for example if you want
most tests within a class not to count towards the score.

```python
from cg_pytest_reporter import weight


@weight(0)
class TestClass:
    # This test case will have a weight of 0 applied, and as such will not count
    # towards the achieved score.
    def test_function():
        assert True

    # This test case will still count towards the score with the default weight
    # of 1.
    @weight(1)
    def test_something_else():
        assert True
```

#### `reason`

Change the reason of failure of the test case. This can be used to give students
a hint where their code is likely to break.

```python
from cg_pytest_reporter import reason

from fibonacci import fibonacci


@reason('Did you start counting at the correct index? (off-by-one error)')
def test_fibonacci():
    assert fibonacci(10) == 55
```

#### `hide_stdout`

When a test fails, the `stdout` that was written while the test was running is
sent along with the result. With the `hide_stdout` decorator you can prevent the
`stdout` from being sent.

```python
from cg_pytest_reporter import hide_stdout


# The string "Hello World!" that was printed to `stdout` will not be sent along
# with the results.
@hide_stdout
def test_failure():
    print('Hello World!')
    assert False
```

This decorator can also be applied to a test class to hide the `stdout` of each
test case within it.

```python
from cg_pytest_reporter import hide_stdout


@hide_stdout
class TestClass:
    def test_failure():
        print('Hello World!')
        assert False

    def test_ok():
        print('Hello World!')
```

#### `hide_stderr`

This works the same as `hide_stdout` except that it will hide the `stderr`
channel instead.

```python
import sys

from cg_pytest_reporter import hide_stderr


# The string "Hello World!" that was printed to `stderr` will not be sent along
# with the results.
@hide_stderr
def test_failure():
    print('Hello World!', file=sys.stderr)
    assert False
```

This decorator can also be applied to a test class to hide the `stderr` of each
test case within it.

```python
import sys

from cg_pytest_reporter import hide_stderr


@hide_stderr
class TestClass:
    def test_failure():
        print('Hello World!', file=sys.stderr)
        assert False

    def test_ok():
        print('Hello World!', file=sys.stderr)
```

#### `hide_output`

A combined version of `hide_stdout` and `hide_stderr`.

```python
import sys

from cg_pytest_reporter import hide_output


# The string "Hello World!" that was printed to `stdout` or `stderr` will not be
# sent along with the results.
@hide_output
def test_failure():
    print('Hello World!')
    print('Hello World!', file=sys.stderr)
    assert False
```

This decorator can also be applied to a test class to hide the output of each
test case within it.

```python
import sys

from cg_pytest_reporter import hide_output


@hide_output
class TestClass:
    def test_failure():
        print('Hello World!', file=sys.stderr)
        assert False

    def test_ok():
        print('Hello World!')
```
