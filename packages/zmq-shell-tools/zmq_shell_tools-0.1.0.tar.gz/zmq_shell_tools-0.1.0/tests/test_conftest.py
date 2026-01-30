from io import BufferedReader, BufferedWriter
from pathlib import Path
from signal import SIGINT, SIGKILL, SIGTERM
from subprocess import Popen
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
def sample_process(run: Callable, parent: Path) -> Generator[Popen, None, None]:
    """
    Handle a simple sample process.
    """
    yield from run(["python", f"{parent}/sample_process.py"])


@parametrize(
    "signal",
    (
        SIGINT,
        SIGTERM,
    ),
    ids=lambda value: value.name,
)
def test_context_manager_process(sample_process: Popen, signal: int) -> None:
    """
    Exit context managers cleanly.
    """
    process = sample_process

    # the process is running
    assert process.poll() is None

    # we expect to have entered the context manager and
    # to run the code block within
    assert isinstance(process.stdout, BufferedReader)
    assert process.stdout.readline() == b"enter\n"
    assert process.stdout.readline() == b"run\n"

    # send a signal and wait for the process to terminate
    process.send_signal(signal)
    stdout, stderr = process.communicate()

    # we expect to have exited the context manager cleanly
    assert stdout == b"exit\n"

    # there is no error message
    assert stderr == b""

    # the process exited without issues
    assert process.returncode == 0


@fixture
def unresponsive_process(run: Callable, parent: Path) -> Generator[Popen, None, None]:
    """
    Handle an unresponsive process.
    """
    yield from run(["python", f"{parent}/unresponsive_process.py"])


def test_kill_process(unresponsive_process: Popen, stop: Callable) -> None:
    """
    Kill processes which don't terminate.
    """
    process = unresponsive_process

    # the process is running
    assert process.poll() is None

    # wait for the script to set up new signal handlers
    assert isinstance(process.stdout, BufferedReader)
    assert process.stdout.readline() == b"ready\n"

    # try to stop the artificially unresponsive process,
    # wait for 1s before killing it
    stdout, stderr = stop(process, timeout=1)

    # we don't expect any output
    assert stdout == b""
    assert stderr == b""

    # the process's returncode reflects that the process had issues exiting
    assert process.returncode == -SIGKILL


def test_communicate_fails(sample_process: Popen, stop: Callable) -> None:
    """
    The process fixture can handle closed stream objects automatically.
    """
    process = sample_process

    assert isinstance(process.stdin, BufferedWriter)
    assert isinstance(process.stdout, BufferedReader)
    assert isinstance(process.stderr, BufferedReader)

    # close to provoke a ValueError due to operations on closed files
    # in `communicate`
    process.stdin.close()
    process.stdout.close()
    process.stderr.close()
