"""Helpers functions that implement boiler plate code used together with
:class:`~cg_feedback_helpers._impl.assertions.Asserter`. It provides support for
easier Input/Output tests.
"""
# Disable this rule as apparently it catches an issue with one of the
# docstring examples. Even when the issue should be fixed, it keeps
# erroring.

import io
import re
import sys
import typing as t
from contextlib import redirect_stdout

__all__ = (
    'capture_output',
    'as_stdin',
    'get_lines_from_buffer',
)


# For ease of use, and in style with ``contextlib``, we do not conform to
# pascal case here.
class capture_output(redirect_stdout):
    """This context manager allows you to capture the output printed to
    ``stdout`` in a :class:`io.StringIO` buffer.

    .. code-block:: python

        >>> from cg_feedback_helpers import helpers
        >>> with helpers.capture_output() as buffer:
        ...     print("Hi")
        >>> print(f"Output was: {buffer.getvalue()}")
        Output was: Hi
        <BLANKLINE>

    """

    def __init__(self) -> None:
        super().__init__(io.StringIO())


# For ease of use, and in style with `contextlib`, we do not conform to
# pascal case here.
class as_stdin:
    """This context manager allows you to provide input to a program by passing
    in the input lines. It temporarily replaces the standard ``stdin`` buffer
    with one containing the specified input lines.

    .. code-block:: python

        >>> from cg_feedback_helpers import helpers
        >>> with helpers.as_stdin("Hi"):
        ...     print(input())
        Hi

    """

    def __init__(self, *input_lines: str) -> None:
        self._buffer = io.StringIO('\n'.join(input_lines))
        self._original_stdin: t.Optional[t.TextIO] = None

    def __enter__(self) -> None:
        self._original_stdin = sys.stdin
        sys.stdin = self._buffer

    def __exit__(self, *exc: object) -> None:
        assert self._original_stdin is not None

        sys.stdin = self._original_stdin
        self._original_stdin = None


def get_lines_from_buffer(
    buffer: io.StringIO,
    *,
    extra_splits: t.List[str] | re.Pattern[str] | None = None,
) -> t.List[str]:
    """Boiler plate to make the use of :class:`capture_output` easier. By
    providing the buffer from :class:`capture_output` you will get the output
    lines, split on the new line, and all lines with just white spaces filtered
    out.

    :param buffer: A :class:`io.StringIO` buffer providing the lines to parse
        and split.
    :param extra_splits: A list of regexes that provide extra split points
        other than ``\\n``. It is your responsibility to guarantee these are
        correct regexes.
    :returns: A list containing the output lines, with the empty lines filtered
        out.

    .. code-block:: python

        >>> from cg_feedback_helpers import helpers
        >>> with helpers.capture_output() as buffer:
        ...     print("something.goes\\nout")
        >>> print(helpers.get_lines_from_buffer(buffer, extra_splits=[r"\\."]))
        ['something', 'goes', 'out']
    """
    if not extra_splits:
        splits = buffer.getvalue().split('\n')
    elif isinstance(extra_splits, re.Pattern):
        splits = re.split(extra_splits.pattern + '|\n', buffer.getvalue())
    else:
        splits = re.split('|'.join(extra_splits) + '|\n', buffer.getvalue())

    return [l for l in splits if l.strip() != '']
