"""Implements the feedback writers providing the output
to the user.
"""

import json
import os
import subprocess
import typing as t
from abc import ABC, abstractmethod

from .makers import PrimedFeedbackMakerF
from .types import (
    NO_FEEDBACK,
    Feedback,
    FeedbackMessage,
    FeedbackPiece,
    FeedbackType,
    NoFeedback,
    is_atv2,
)


def json_dumps(obj: object) -> str:
    """Dump an object to JSON without any extra formatting."""
    return json.dumps(obj, separators=(',', ':'))


class FeedbackAssertionError(SystemExit):
    def __init__(self, feedback: Feedback) -> None:
        """Exception raised when an assertion fails.

        Inherits from :class:`SystemExit` to make the execution exit gracefully.

        ``NO_FEEDBACK`` passes ``1`` to the constructor of :class:`SystemExit`.

        :param feedback: The feedback message to display the user.
        """
        if isinstance(feedback, NoFeedback):
            super().__init__(1)
        else:
            super().__init__(feedback)


class Writer(ABC):
    """Base writer interface.

    Handles the opening and closing of resouces (files, file descriptors,
    streams, and so on).

    Also defines how the output is provided to the user. Current
    implementations are:

    * :class:`StructuredOutputWriter`

    * :class:`ExceptionsWriter`

    :param is_atv2: ``True`` if the run environment is AutoTest V2.
    """

    @abstractmethod
    def finalize(self) -> None:
        """Cleans up the resources used by the writer.

        :class:`~cg_feedback_helpers._impl.assertions.Asserter` calls this
        method when exiting to make sure no open handles are left.
        """

    @abstractmethod
    def write(
        self,
        cond: bool,
        maker: PrimedFeedbackMakerF,
        positive_feedback: t.Optional[Feedback],
        negative_feedback: t.Optional[Feedback],
    ) -> None:
        """Defines how the feedback is provided to the user.

        :param cond: The condition that must be satisfied for the assertion to
            pass. If resolved to ``True``, the positive feedback (or its default)
            is output, otherwise the negative feedback (or its default) is output.
        :param maker: The feedback maker function.
        :param positive_feedback: The positive feedback override.
        :param negative_feedback: The negative feedback override.
        """


class StructuredOutputWriter(Writer):
    def __init__(self) -> None:
        """Writer that uses structured output to report feedback.

        It also rises a :class:`FeedbackAssertionError` without message in
        case of failures.

        If the code is running on ATv2, or the environment variable
        ``CG_FEEDBACK_HELPERS_TRUNCATE`` is set, it uses the ``cg truncate``
        command under the hood.
        """
        self.__output_file: t.Optional[t.IO[bytes]] = None
        self.__proc: t.Optional[subprocess.Popen] = None

    @property
    def _output_file(self) -> t.IO[bytes]:
        if self.__output_file is None:
            assert self.__proc is None, 'We are in an illegal state!'
            self.__proc, self.__output_file = self._open_output()
        return self.__output_file

    @staticmethod
    def _open_output() -> t.Tuple[subprocess.Popen | None, t.IO[bytes]]:
        if is_atv2() or 'CG_FEEDBACK_HELPERS_TRUNCATE' in os.environ:
            proc = subprocess.Popen(
                ['cg', 'truncate'],
                # The `cg` command already does buffering for us, so disable
                # buffering.
                bufsize=0,
                stdin=subprocess.PIPE,
                close_fds=False,
            )
            assert proc.stdin is not None
            output_file = proc.stdin
            return proc, output_file

        return None, open(2, 'wb', buffering=0)

    def _maybe_write_structured_feedback(
        self,
        feedback: Feedback,
        ftype: FeedbackType,
    ) -> None:
        if not isinstance(feedback, NoFeedback):
            message = FeedbackMessage(
                tag='feedback',
                contents=[
                    FeedbackPiece(
                        value=feedback,
                        sentiment=ftype.value,
                    ),
                ],
            )
            self._output_file.write(
                (json_dumps(message) + '\n').encode('utf8')
            )

    def finalize(self) -> None:
        output_file = self.__output_file
        if output_file is not None:
            self._output_file.close()
            self.__output_file = None

        proc = self.__proc
        if proc is not None:
            proc.wait()
            self.__proc = None

    def write(
        self,
        cond: bool,
        maker: PrimedFeedbackMakerF,
        positive_feedback: t.Optional[Feedback],
        negative_feedback: t.Optional[Feedback],
    ) -> None:
        if cond:
            self._maybe_write_structured_feedback(
                maker(positive_feedback, FeedbackType.POSITIVE),
                FeedbackType.POSITIVE,
            )
        else:
            self._maybe_write_structured_feedback(
                maker(negative_feedback, FeedbackType.NEGATIVE),
                FeedbackType.NEGATIVE,
            )
            raise FeedbackAssertionError(NO_FEEDBACK)


class ExceptionsWriter(Writer):
    def __init__(self) -> None:
        """Writer that uses exceptions to report negative feedback.

        Positive feedback is printed to standard output.

        This can  also be used as a debug writer as the text is clearly
        written in the output, instead of formatted for structured output
        feedback message format.
        """
        self.__output_file: t.Optional[t.IO[bytes]] = None

    @property
    def _output_file(self) -> t.IO[bytes]:
        if self.__output_file is None:
            # We don't want to close file descriptor 1.
            self.__output_file = open(1, 'wb', buffering=0)
        return self.__output_file

    def finalize(self) -> None:
        """You should call this method at the end of your test routine to make
        sure file handles are correctly closed.
        """
        output_file = self.__output_file
        if output_file is not None:
            self._output_file.close()
            self.__output_file = None

    def write(
        self,
        cond: bool,
        maker: PrimedFeedbackMakerF,
        positive_feedback: t.Optional[Feedback],
        negative_feedback: t.Optional[Feedback],
    ) -> None:
        if cond:
            feedback = maker(positive_feedback, FeedbackType.POSITIVE)
            if not isinstance(feedback, NoFeedback):
                self._output_file.write((feedback + '\n').encode('utf8'))
        else:
            raise FeedbackAssertionError(
                maker(negative_feedback, FeedbackType.NEGATIVE)
            )
