import sys
from time import sleep
from typing import Any

from zmq_shell_tools.signal import Shield


def stdout(message: str) -> None:
    """
    Immediately write a messsage to stdout.

    Arguments:
        message: the message to print.
    """
    sys.stdout.write(f"{message}\n")
    sys.stdout.flush()


class TestContextManager:
    """
    A context manager printing enter and exit messages on
    entering and leaving the context, respectively.
    """

    def __enter__(self) -> None:
        """
        Hook executed on entering the context.

        It prints an "enter" message to stdout.
        """
        stdout("enter")

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """
        Hook executed on entering the context.

        It prints an "exit" message to stdout.
        """
        stdout("exit")


# enter the shielded and test context
with Shield(), TestContextManager():
    # signal that we entered the context
    stdout("ready")

    # simulate some processing
    sleep(1)

# print additional message for testing by its presence or absence
stdout("not printed when interrupted")
