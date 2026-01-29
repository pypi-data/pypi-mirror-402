"""The types used in the `cg_feedback_helpers` package."""

import os
import typing as t
from enum import Enum


def is_atv2() -> bool:
    """Detects whether the code is running on ATv2.

    :returns: Whether ATv2 environment was detected.
    """
    return os.getenv('CG_ATV2') == 'true'


# This class allows us to have a type for `NO_FEEDBACK` that can be used in the
# general `Feedback` UnionType.
class NoFeedback:
    """Sentinel used to inform the helpers to not print any feedback."""

    # Coverage is disabled as we do not really care about what the string
    # representation of this is.
    def __repr__(self) -> str:  # pragma: no cover
        return 'NoFeedback'


NO_FEEDBACK = NoFeedback()
"""Constant that represents the "do not print any feedback" case.
"""

Feedback = t.Union[str, NoFeedback]
"""- None, empty string = use default feedback
- non-empty string = custom feedback
- NoFeedback = Do not print any feedback
"""


class FeedbackType(Enum):
    """Currently supported feedback types."""

    #: Feedback provided in case of assertions passing.
    POSITIVE = 'positive'
    #: Feedback provided in case of assertions failing.
    NEGATIVE = 'negative'


class FeedbackPiece(t.TypedDict):
    """A plaintext piece of feedback. Currently, the package
    does not support markdown feedback.
    """

    #: The content of the feedback.
    value: str
    #: The sentiment the feedback should have (neutral not supported).
    sentiment: t.Literal['positive', 'negative']


class FeedbackMessage(t.TypedDict):
    """The message to be sent for each piece of feedback"""

    #: The message tag.
    tag: t.Literal['feedback']
    #: The list of feedback pieces
    contents: t.List[FeedbackPiece]


BASE_FILTER_OUT_GLOBALS = [
    '__name__',
    '__doc__',
    '__package__',
    '__loader__',
    '__spec__',
    '__annotations__',
    '__builtins__',
    '__file__',
    '__cached__',
    '__warningregistry__',
    'asserter',
    'helpers',
    'cg_feedback_helpers',
]
