"""This module contains decorators that can be used to mark certain properties
of a test function or class.

See README.md for more information and examples.
"""

import typing as t

import pytest

T = t.TypeVar('T', bound=t.Callable)


def __getattr__(name: str) -> t.Any:
    if name in (
        'suite_name',
        'suite_weight',
        'name',
        'description',
        'weight',
        'reason',
        'hide_stdout',
        'hide_stderr',
    ):
        return getattr(pytest.mark, f'cg_{name}')

    raise AttributeError(name)


def hide_output(func: T) -> T:
    return pytest.mark.cg_hide_stdout(pytest.mark.cg_hide_stderr(func))
