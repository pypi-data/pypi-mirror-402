from signal import SIGINT, SIGTERM, signal
from sys import exit
from types import FrameType, TracebackType
from typing import Callable, Self

from loguru import logger

_SIGNALS = (SIGINT, SIGTERM)
"""
Signals on which to exit gracefully.
"""


def _exit(signum: int, frame: FrameType | None) -> None:
    """
    Exit signal handler.

    Arguments:
        signum: the number of the triggering signal.
        frame: the corresponding stack frame object.
    """
    exit()


def interruptable() -> None:
    """
    Exit on `SIGINT` and `SIGTERM` signals.
    """
    for signum in _SIGNALS:
        signal(signum, _exit)


class Shield:
    """
    A context manager letting the enclosed code block finish before
    exiting the script due to a received SIGINT or SIGTERM signal.
    """

    interrupted: bool
    """
    Flag indicating that a SIGINT or SIGTERM signal was received.
    """

    _handlers: list[Callable | int | None]
    """
    Temporary container for original signal handlers.
    """

    def __init__(self):
        """
        Hook executed upon class initialization.

        It sets the instance's `interrupted` attribute to `False`.
        """
        self.interrupted = False

    def _delay(self, signum: int, frame: FrameType | None) -> None:
        """
        A signal handler registering a SIGINT or SIGTERM signal
        for a delayed process exit.

        It sets the `interrupted` attribute to `True` on a received
        SIGINT or SIGTERM.
        On a second SIGINT or SIGTERM, it exits the process.

        Arguments:
            signum: the number of the received signal.
            frame: the corresponding stack frame object.
        """
        if self.interrupted:
            exit()

        self.interrupted = True

    def __enter__(self) -> Self:
        """
        Hook executed on entering the context.

        It replaces the signal handlers such that SIGINT and SIGTERM
        do not interrupt or exit the process right away.

        Returns:
            the reference to itself.
        """
        self._handlers = [signal(signum, self._delay) for signum in _SIGNALS]
        logger.debug("set delaying signal handlers")

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        """
        Hook executed on leaving the context.

        It restores the shielding signal handlers with the original
        ones if no SIGINT or SIGTERM signal was received during
        execution of the shielded code block.
        Otherwise, it exits the process.

        Arguments:
            exc_type: the exception class.
            exc_value: the instance of the exception class.
            exc_tb: the traceback of the instance of the exception class.
        """
        if self.interrupted:
            logger.debug("exiting due to previously received interrupting signal")
            exit()
        else:
            # restore original signal handlers
            for signum, handler in zip(_SIGNALS, self._handlers):
                signal(signum, handler)

            # clean up temporary signal handler container
            del self._handlers

            logger.debug("restored original signal handlers")
