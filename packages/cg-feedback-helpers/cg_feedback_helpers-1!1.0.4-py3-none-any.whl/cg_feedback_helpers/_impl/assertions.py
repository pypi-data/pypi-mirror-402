"""Definition of the :class:`Asserter`. Provides also a default instance that
can be easily used importing `asserter`.
"""

import atexit
import math
import os
import sys
import typing as t
from types import ModuleType

from .config import Config, ExistFeedbackMakerInput, ExpectFeedbackMakerInput
from .makers import PrimedFeedbackMakerF
from .types import BASE_FILTER_OUT_GLOBALS, NO_FEEDBACK, Feedback
from .writers import ExceptionsWriter, StructuredOutputWriter

_T = t.TypeVar('_T')


class Asserter:
    def __init__(self, config: Config = Config()) -> None:
        """This class provides the implementaion of the assertion methods of
        the feedback helpers.

        Each assertion can output either a positive or a negative feedback,
        depending on whether the assertion passes or fails. A default feedback
        maker is defined in the configuration.

        You have two ways of overriding the feedback:

        * Provide a custom piece of feedback for each assertion using
          ``positive_feedback`` or ``negative_feedback`` keyword arguments;

        * Define custom feedback makers in the
          :class:`~cg_feedback_helpers._impl.config.Config` when instantiating
          any implementation of :class:`Asserter`.

        :param config: The configuration overrides. Check
            :class:`~cg_feedback_helpers._impl.config.Config`.
        """
        self._config = config
        atexit.register(self.finalize)

    def finalize(self) -> None:
        """You should call this method at the end of your test routine to make
        sure file handles are correctly closed.
        """
        self._config.writer.finalize()

    def _assert(
        self,
        cond: bool,
        maker: PrimedFeedbackMakerF,
        positive_feedback: t.Optional[Feedback],
        negative_feedback: t.Optional[Feedback],
    ) -> None:
        """This method is used by the asserter to provide the correct feedback when
        called.

        :param cond: The boolean condition provided by the assertion. If true, it
            means the assertion passed and the ``positive_feedback`` should be
            displayed, otherwise the ``negative_feedback``.
        :param maker: The feedback maker object that will make sure the feedback
            is hydrated with the correct default value if the user provided none.
        :param positive_feedback: Overrides the feedback the user receives if the
            assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if the
            assertion fails.
        """
        self._config.writer.write(
            cond, maker, positive_feedback, negative_feedback
        )

    def variable_exists(
        self,
        varname: str,
        variables: t.Dict[str, t.Any],
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts whether a variable exists in the given set of variables.

        :param varname: The name of the variable that should exist.
        :param variables: The set of variables. Usually, you want this to be
            ``globals()``.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExistFeedbackMakerInput('variable', varname, repr(varname))
        self._assert(
            varname in variables,
            self._config.exist_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def is_set(
        self,
        key: str,
        dictionary: t.Dict[str, t.Any],
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts whether a certain key exists in the given dictionary.

        It currently only works with string-keys.

        :param key: The key that should exist in the dictionary.
        :param dictionary: The dictionary that should contain the provided key.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExistFeedbackMakerInput('key', key, repr(key))
        self._assert(
            key in dictionary,
            self._config.exist_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def is_not_set(
        self,
        key: str,
        dictionary: t.Dict[str, t.Any],
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts whether a certain key does not exist in the given dictionary.

        It currently only works with string-keys.

        :param key: The key that should not exist in th dictionary.
        :param dictionary: The dictionary that should not contain the provided
            key.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExistFeedbackMakerInput('key', key, repr(key))
        self._assert(
            key not in dictionary,
            self._config.not_exist_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def only_defined_names(
        self,
        keys: t.List[str],
        dictionary: t.Dict[str, t.Any],
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that only certain keys are exist in the given dictionary.

        It currently only works with string-keys.

        Other than the keys provided, a set of keys is added to make sure that
        this works as expected also with ``globals()``.

        :param keys: The list of the only keys that should exist in the
            dictionary.
        :param dictionary: The dictionary that should only contain the provided
            keys.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExistFeedbackMakerInput('only keys', keys, keys)
        filter_out = BASE_FILTER_OUT_GLOBALS + keys
        self._assert(
            not any(x not in filter_out for x in dictionary.keys()),
            self._config.exist_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def not_equals(
        self,
        val: _T,
        not_expected: _T,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the two values are not equal.

        :param val: The value to check.
        :param not_expected: The value that ``val`` should not be equal to.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExpectFeedbackMakerInput(
            'value', val, not_expected, not_expected
        )
        self._assert(
            val != not_expected,
            self._config.not_expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def equals(
        self,
        val: _T,
        expected: _T,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the two values are equal.

        :param val: The value to check.
        :param expected: The expected value ``val`` should be equal to.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExpectFeedbackMakerInput('value', val, expected, expected)
        self._assert(
            val == expected,
            self._config.expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def equals_float(
        self,
        val: float,
        expected: float,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the two floating point values are equal.

        It uses ``math.isclose`` with the default relative and absolute
        tolerances.

        :param val: The value to check.
        :param expected: The expected value ``val`` should be equal to.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExpectFeedbackMakerInput('float value', val, expected, expected)
        self._assert(
            math.isclose(val, expected),
            self._config.expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def is_of_type(
        self,
        val: t.Any,
        expected: t.Type,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the value is of the provided type.

        :param val: The value to check.
        :param expected: The type ``val`` should be.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        typ = type(val)
        inp = ExpectFeedbackMakerInput('type', typ, expected, expected)
        self._assert(
            typ == expected,
            self._config.expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def not_none(
        self,
        val: object,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the value is not ``None``.

        :param val: The value that should not be ``None``.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExpectFeedbackMakerInput('value', val, None, 'None')
        self._assert(
            val is not None,
            self._config.not_expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def has_length(
        self,
        val: t.Sequence,
        expected_length: int,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the provided sequence is of a certain length.

        :param val: The sequence to check.
        :param expected_length: The length ``val`` should have.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        length = len(val)
        inp = ExpectFeedbackMakerInput(
            'length', length, expected_length, expected_length
        )
        self._assert(
            length == expected_length,
            self._config.expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def string_contains(
        self,
        val: str,
        expected: str,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the a certain string contains the provided value.

        :param val: The value that should exist in the string.
        :param expected: The string that should contain ``val``.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExpectFeedbackMakerInput('substring', val, expected, expected)
        self._assert(
            expected in val,
            self._config.expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def is_imported(
        self,
        module_name: str,
        modules: t.Dict[str, ModuleType],
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Assrets that the provided module exists in a certain set of modules.

        Usually, you want ``modules`` to be ``sys.modules``.

        :param module_name: The module that should be imported.
        :param modules: The dictionary of imported modules.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExistFeedbackMakerInput('module', module_name, module_name)
        self._assert(
            module_name in modules,
            self._config.exist_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def file_exists(
        self,
        file_path: str | os.PathLike[str],
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the provided file exists in the file system.

        :param file_path: The file that should exist.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExistFeedbackMakerInput('file', file_path, file_path)
        self._assert(
            os.path.exists(file_path),
            self._config.exist_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def has_attr(
        self,
        attr: str,
        obj: object,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that a given attribute exists in a certain object.

        :param attr: The attribute that should exist in the object.
        :param obj: The object that should have the given attribute.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExistFeedbackMakerInput('attribute', attr, attr)
        self._assert(
            hasattr(obj, attr),
            self._config.exist_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def is_true(
        self,
        val: bool,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the value is ``True``.

        :param val: The value to check.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExpectFeedbackMakerInput('boolean', val, True, True)
        self._assert(
            val is True,
            self._config.expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def is_false(
        self,
        val: bool,
        *,
        positive_feedback: t.Optional[Feedback] = None,
        negative_feedback: t.Optional[Feedback] = None,
    ) -> None:
        """Asserts that the value is ``False``.

        :param val: The value to check.
        :param positive_feedback: Overrides the feedback the user receives if
            the assertion passes.
        :param negative_feedback: Overrides the feedback the user receives if
            the assertion fails.
        """
        inp = ExpectFeedbackMakerInput('boolean', val, False, False)
        self._assert(
            val is False,
            self._config.expect_feedback_maker.get_feedback_maker(inp),
            positive_feedback,
            negative_feedback,
        )

    def never(
        self,
        feedback: Feedback,
    ) -> None:
        """Assertion that always fails. Should be used in branches of execution
        that should not be called.

        :param feedback: The feedback to provide the user in case this
            assertion is called.
        """
        inp = ExpectFeedbackMakerInput(
            'assertion', 'reached', 'reached', 'reached'
        )
        self._assert(
            False,
            self._config.not_expect_feedback_maker.get_feedback_maker(inp),
            NO_FEEDBACK,
            feedback,
        )

    def emit_success(
        self, *, feedback: t.Optional[Feedback] = None
    ) -> t.NoReturn:
        """Writes to the configured output a message giving the user feedback
        that all the assertions have passed and he successfully passed the
        tests.

        The asserter is finalized and the execution terminated.

        :param feedback: Overrides the default feedback displayed to the user.
        """
        self._assert(
            True,
            lambda f, __: f if f is not None else self._config.success_message,
            feedback,
            NO_FEEDBACK,
        )
        sys.exit(0)


asserter = Asserter(config=Config(writer=StructuredOutputWriter()))
"""Default asserter exported for comodity. It will use all the default config.
"""

pytest_asserter = Asserter(config=Config(writer=ExceptionsWriter()))
"""Default asserter setup for use in the ``Pytest`` block, exported for
comodity.
"""
