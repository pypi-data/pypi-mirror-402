"""Implements the feedback makers, which define how the feedback
is provided to the user in case no overrides are set.
"""

import typing as t
from dataclasses import dataclass

from .types import Feedback, FeedbackType, NoFeedback

_Y = t.TypeVar('_Y')


@dataclass
class ExpectFeedbackMakerInput(t.Generic[_Y]):
    """Provides the parameters for :class:`ExpectFeedbackMaker` instances.
    Defines the contents of the feedback provided to the user.
    """

    #: What is the feedback about. Should be just a name.
    what: str
    #: The value that was received.
    value: _Y
    #: The raw value that was expected.
    expected_raw: _Y
    #: The representation of the expected value.
    expected: t.Union[_Y, str]

    def get_expected_repr(self, with_type: bool) -> str:
        if with_type:
            return f'{self.expected_raw!r} {type(self.expected_raw)}'
        return repr(self.expected_raw)

    def get_value_repr(self, with_type: bool) -> str:
        if with_type:
            return f'{self.value!r} {type(self.value)}'
        return repr(self.value)


@dataclass
class ExistFeedbackMakerInput(t.Generic[_Y]):
    """Provides the parameters for :class:`ExistFeedbackMaker` instances.
    Defines the contents of the feedback provided to the user.
    """

    #: What is the feedback about. Should be just a name.
    what: str
    #: The raw value that was expected.
    expected_raw: _Y
    #: The representation of the expected value.
    expected: t.Union[_Y, str]

    def get_expected_repr(self, with_type: bool) -> str:
        if with_type:
            return f'{self.expected_raw!r} {type(self.expected_raw)}'
        return repr(self.expected_raw)


ExpectFeedbackMakerF = t.Callable[[ExpectFeedbackMakerInput], Feedback]
"""A function that takes a :class:`ExpectFeedbackMakerInput` instance and
produces a valid piece of feedback.
"""
ExistFeedbackMakerF = t.Callable[[ExistFeedbackMakerInput], Feedback]
"""A function that takes a :class:`ExistFeedbackMakerInput` instance and
produces a valid piece of feedback.
"""


@dataclass
class DefaultExpectFeedback:
    """Default feedback maker functions for :class:`ExpectFeedbackMaker`."""

    #: Maker function for positive feedback.
    positive: ExpectFeedbackMakerF
    #: Maker function for negative feedback.
    negative: ExpectFeedbackMakerF


@dataclass
class DefaultExistFeedback:
    """Default feedback maker functions for :class:`ExistFeedbackMaker`."""

    #: Maker function for positive feedback.
    positive: ExistFeedbackMakerF
    #: Maker function for negative feedback.
    negative: ExistFeedbackMakerF


#: A function that has been primed with configuration data and can be used
#: to produce feedback pieces from the user override.
PrimedFeedbackMakerF = t.Callable[
    [t.Optional[Feedback], FeedbackType], Feedback
]


@dataclass
class ExpectFeedbackMaker:
    """Factory class used to generate feedback based on user input data and the
    defaults provided when configuring an implementaion of the
    :class:`~cg_feedback_helpers._impl.assertions.Asserter`.
    """

    defaults: DefaultExpectFeedback

    def get_feedback_maker(
        self,
        inp: ExpectFeedbackMakerInput,
    ) -> PrimedFeedbackMakerF:
        """Generates a primed function that takes a potential user feedback
        override, and the type of feedback to be produced.

        If the custom feedback is ``None``, the ``default[typ]`` is used instead.
        The generated piece of feedback is guaranteed to not be ``None``.

        :param inp: The input data for the feedback maker function.
        :returns: A function that produces a piece of feedback.
        """

        def get_feedback(
            custom: t.Optional[Feedback],
            typ: FeedbackType,
        ) -> Feedback:
            # Simple case: no feedback symbol is valid feedback.
            if isinstance(custom, NoFeedback):
                return custom

            # Simple case: any non-empty string is valid feedback.
            if custom is not None and custom.strip() != '':
                return custom

            if typ is FeedbackType.NEGATIVE:
                return self.defaults.negative(inp)
            return self.defaults.positive(inp)

        return get_feedback


@dataclass
class ExistFeedbackMaker:
    """Factory class used to generate feedback based on user input data and the
    defaults provided when configuring an implementation of the
    :class:`~cg_feedback_helpers._impl.assertions.Asserter`.
    """

    defaults: DefaultExistFeedback

    def get_feedback_maker(
        self,
        inp: ExistFeedbackMakerInput,
    ) -> PrimedFeedbackMakerF:
        """Generates a primed function that takes a potential user feedback
        override, and the type of feedback to be produced.

        If the custom feedback is ``None``, the ``default[typ]`` is used instead.
        The generated piece of feedback is guaranteed to not be ``None``.

        :param inp: The input data for the feedback maker function.
        :returns: A function that produces a piece of feedback.
        """

        def get_feedback(
            custom: t.Optional[Feedback],
            typ: FeedbackType,
        ) -> Feedback:
            # Simple case: no feedback symbol is valid feedback.
            if isinstance(custom, NoFeedback):
                return custom

            # Simple case: any non-empty string is valid feedback.
            if custom is not None and custom.strip() != '':
                return custom

            if typ is FeedbackType.NEGATIVE:
                return self.defaults.negative(inp)
            return self.defaults.positive(inp)

        return get_feedback
