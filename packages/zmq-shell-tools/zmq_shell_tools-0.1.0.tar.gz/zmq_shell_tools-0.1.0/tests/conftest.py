from contextlib import closing
from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, socket
from subprocess import PIPE, Popen, TimeoutExpired
from typing import Any, Callable, Generator

from loguru import logger
from pytest import fixture

LOCALHOST = "127.0.0.1"
"""IPv4 address for the localhost loopback interface."""


def free_tcp_port() -> int:
    """
    Get a free TCP socket chosen by the operating system.

    Returns:
        a free TCP port.
    """
    # see https://stackoverflow.com/a/45690594
    # and https://docs.python.org/3/library/socket.html#example
    with closing(socket(AF_INET, SOCK_STREAM)) as s:
        # reuse the address to avoid "already in use"-errors
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # use 0 to let the OS choose
        s.bind((LOCALHOST, 0))

        # the second argument is the port
        return s.getsockname()[1]


@fixture(scope="session")
def tcp() -> str:
    """
    Get a TCP address on localhost.

    Arguments:
        free_tcp_port: a free TCP port.

    Returns:
        the free TCP address on localhost.
    """
    address = f"tcp://{LOCALHOST}:{free_tcp_port()}"

    logger.debug(f"retrieved address {address}")

    return address


def wait(
    process: Popen,
    timeout: int | None = None,
) -> tuple[bytes, bytes] | tuple[None, None]:
    """
    Wait for a subprocess to finish and try to return its stdout and stderr contents.

    Arguments:
        process: the subprocess instance
        timeout: the timeout to wait for the process to terminate.

    Raises:
        TimeoutExpired: when the process did not terminate before the timeout passed.

    Returns:
        a tuple of the contents of stdout and stderr in bytes or, if communication failed,
        a tuple of `None`s.
    """
    try:
        return process.communicate(timeout=timeout)
    except ValueError:
        # might be caused by operation on closed standard streams,
        # so just wait for the process to finish
        process.wait(timeout=timeout)
        return None, None


@fixture(scope="class")
def stop() -> Callable:
    """
    Provide a subprocess stopping routine.

    Returns:
        a routine handling the stopping of a subprocess.
    """

    def _stop(
        process: Popen,
        timeout: int | None = None,
    ) -> tuple[bytes, bytes] | tuple[None, None]:
        """
        Arguments:
            process: the subprocess instance to stop.
            timeout: the timeout for a graceful termination.

        Returns:
            a tuple of the contents of stdout and stderr in bytes or, if communication failed,
            a tuple of `None`s.
        """
        if process.poll() is not None:
            logger.debug(f"process {process} already returned")

            # the process already returned, mimic the returned stdout and stderr values
            return b"", b""

        try:
            estimate = f"wait {timeout:d}s" if timeout is not None else "wait"
            logger.debug(f"{estimate} for process {process} to terminate gracefully")

            # we need to actively terminate indefinitely running processes
            process.terminate()

            # return stdout and stderr
            return wait(process, timeout=timeout)
        except TimeoutExpired:
            logger.debug(f"kill process {process} forcefully")

            # kill the process as it didn't terminate by itself
            process.kill()

            # return stdout and stderr
            return wait(process)

    return _stop


@fixture(scope="class")
def run(stop: Callable) -> Callable:
    """
    Provide a subprocess running routine.

    Arguments:
        stop: the subprocess stopping routine.

    Returns:
        a routine defining how to run a subprocess.
    """

    def _run(
        *args: Any,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> Generator[Popen, None, None]:
        """
        Run a subprocess, teared down after the test scope ended.

        Arguments:
            *args: positional arguments passed to [`Popen`][subprocess.Popen].
            timeout: the timeout to wait before killing the process forcefully.
            **kwargs: keyword arguments passed to [`Popen`][subprocess.Popen].

        Yields:
            the running subprocess.
        """
        # set and update default settings
        settings: dict[str, Any] = dict(
            text=False,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        settings.update(kwargs)

        # run the process
        process = Popen(*args, **settings)

        # yield the process to the test
        logger.debug(f"yield process {process}")
        yield process

        # teardown
        logger.debug(f"tearing down process {process}")
        stop(process, timeout=timeout)

    return _run
