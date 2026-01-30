import sys
from time import sleep
from typing import Any

from zmq_shell_tools.signal import interruptable

# add exit handlers for SIGINT and SIGTERM
interruptable()


def stdout(message: str) -> None:
    """
    Write to stdout immediately.

    Arguments:
       message: the message to write to stdout.
    """
    sys.stdout.write(f"{message}\n")
    sys.stdout.flush()


class TestContextManager:
    """
    Write to stdout when entering and exiting the context.
    """

    def __enter__(self) -> None:
        """
        Hook executed on entering the context.
        """
        stdout("enter")

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """
        Hook executed on exiting the context.
        """
        stdout("exit")


with TestContextManager():
    # "enter" has been written
    stdout("run")

    # simulate indefinitely running process
    while True:
        sleep(1)

    stdout("this will never be written")

# "exit" has been written
