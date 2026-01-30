from io import BufferedReader
from pathlib import Path
from signal import SIGABRT, SIGHUP, SIGINT, SIGKILL, SIGQUIT, SIGTERM
from subprocess import Popen
from time import sleep, time
from typing import Callable, Generator

from pytest import fixture, mark

parametrize = mark.parametrize


@fixture(scope="module")
def parent() -> Path:
    """
    Get the absolute parent directory of this module.
    """
    return Path(__file__).parent.absolute()


@fixture
def process(run: Callable, parent: Path) -> Generator[Popen, None, None]:
    """
    Run the sample process featuring the `Shield` class.
    """
    yield from run(["python", f"{parent}/sample_shield.py"])


def test_sample_shield(process: Popen):
    """
    The sample script prints these messages on stdout.
    """
    # wait for the process to terminate
    stdout, stderr = process.communicate(timeout=2)

    # the process prints these messages
    assert stdout == (b"enter\nready\nexit\nnot printed when interrupted\n")

    # process exited normally
    assert process.returncode == 0


@parametrize(
    "signum",
    (
        SIGINT,
        SIGTERM,
    ),
)
def test_shield_single_signal(process: Popen, signum: int) -> None:
    """
    A single signal leads to termination right after the shielded code block finished.
    """
    assert isinstance(process.stdout, BufferedReader)

    # wait for the process to enter the shielded context
    assert process.stdout.readline() == b"enter\n"
    assert process.stdout.readline() == b"ready\n"

    # start timestamp
    start = time()

    # send the signal
    process.send_signal(signum)

    # wait for the process to terminate
    stdout, stderr = process.communicate(timeout=2)

    # end timestamp
    end = time()

    # we waited for at least the sleep time of the shielded context
    assert end - start >= 1

    # expected absence of message "not printed when interrupted"
    assert stdout == b"exit\n"

    # process exited normally
    assert process.returncode == 0


@parametrize(
    "signum1",
    (
        SIGINT,
        SIGTERM,
    ),
)
@parametrize(
    "signum2",
    (
        SIGINT,
        SIGTERM,
    ),
)
def test_shield_double_signal(process: Popen, signum1: int, signum2: int) -> None:
    """
    Sending two handled signals exits the process right away, but still does call
    the context managers __exit__ hooks.
    """
    assert isinstance(process.stdout, BufferedReader)

    # wait for the process to enter the shielded context
    assert process.stdout.readline() == b"enter\n"
    assert process.stdout.readline() == b"ready\n"

    # start timestamp
    start = time()

    # send the first signal
    process.send_signal(signum1)

    # give the signal time to be handled by the process's signal handler
    sleep(0.1)

    # send the second signal
    process.send_signal(signum2)

    # wait for the process to terminate
    stdout, stderr = process.communicate(timeout=2)

    # end timestamp
    end = time()

    # we finished well under the sleep time of the shielded context
    assert end - start < 1

    # context manager's __exit__ hook still executed;
    # expected absence of message "not printed when interrupted"
    assert stdout == b"exit\n"

    # process exited normally
    assert process.returncode == 0


@parametrize(
    "signum",
    (
        SIGHUP,
        SIGQUIT,
        SIGABRT,
        SIGKILL,
    ),
)
def test_shield_unhandled_signals(process: Popen, signum: int) -> None:
    """
    These unhandled signals lead to direct termination without invoking __exit__ hooks.
    """
    assert isinstance(process.stdout, BufferedReader)

    # wait for the process to enter the shielded context
    assert process.stdout.readline() == b"enter\n"
    assert process.stdout.readline() == b"ready\n"

    # send the signal
    process.send_signal(signum)

    # wait for the process to terminate
    stdout, stderr = process.communicate(timeout=2)

    # process exited immediately without calling __exit__ hooks;
    # expected absence of both messages
    # "exit" and "not printed when interrupted"
    assert stdout == b""

    # the return code reflects the unhandled signal number
    assert process.returncode == -signum
