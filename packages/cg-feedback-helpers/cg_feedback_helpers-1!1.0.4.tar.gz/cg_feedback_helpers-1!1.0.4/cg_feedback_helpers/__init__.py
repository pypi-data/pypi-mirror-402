"""This package provides support for CodeGrades Feedback messages in AutoTest
V2. It was developed mainly to be used with the ``Simple Python Test`` block
and provides an assertion-based API to provide feedback during the execution of
a piece of student code, as well as providing some useful helper functions to
more easily do input/output testing on said code.

To install locally, run ``python3 -mpip install cg-feedback-helpers``. To start,
take a look at :class:`~cg_feedback_helpers._impl.assertions.Asserter`.
"""

from . import helpers
from ._impl.assertions import Asserter, asserter, pytest_asserter
from ._impl.compatibility_layer import (
    assert_equals,
    assert_file_exists,
    assert_has_length,
    assert_is_imported,
    assert_is_of_type,
    assert_is_set,
    assert_not_equals,
    assert_not_none,
    emit_success,
)
from ._impl.config import (
    Config,
    DefaultExistFeedback,
    DefaultExpectFeedback,
    ExistFeedbackMaker,
    ExistFeedbackMakerInput,
    ExpectFeedbackMaker,
    ExpectFeedbackMakerInput,
)
from ._impl.makers import (
    ExistFeedbackMakerF,
    ExpectFeedbackMakerF,
    PrimedFeedbackMakerF,
)
from ._impl.types import NO_FEEDBACK, Feedback, FeedbackType, is_atv2
from ._impl.writers import (
    ExceptionsWriter,
    FeedbackAssertionError,
    StructuredOutputWriter,
    Writer,
)

__all__ = (
    'Asserter',
    'asserter',
    'helpers',
    'NO_FEEDBACK',
    'FeedbackType',
    'Feedback',
    'FeedbackAssertionError',
    'Config',
    'ExpectFeedbackMaker',
    'ExistFeedbackMaker',
    'DefaultExistFeedback',
    'DefaultExpectFeedback',
    'ExpectFeedbackMakerInput',
    'ExistFeedbackMakerInput',
    'ExpectFeedbackMakerF',
    'ExistFeedbackMakerF',
    'PrimedFeedbackMakerF',
    'assert_is_set',
    'assert_equals',
    'assert_not_equals',
    'assert_is_of_type',
    'assert_has_length',
    'assert_not_none',
    'assert_file_exists',
    'assert_is_imported',
    'emit_success',
    'pytest_asserter',
    'Writer',
    'StructuredOutputWriter',
    'ExceptionsWriter',
    'is_atv2',
)
