import sys
from io import BufferedReader, BufferedWriter
from subprocess import Popen
from typing import Callable, Generator
from warnings import warn

from loguru import logger
from pytest import fixture, mark

parametrize = mark.parametrize


@fixture(scope="class")
def push(tcp: str, run: Callable) -> Generator[Popen, None, None]:
    """
    Run the PUSH socket without echoing to stdout.
    """
    yield from run(["zmq", "push", "--debug", "--bind", tcp])


@fixture(scope="class")
def pull(tcp: str, run: Callable) -> Generator[Popen, None, None]:
    """
    Run the PULL socket.
    """
    yield from run(["zmq", "pull", "--debug", "--connect", tcp])


@fixture(scope="class")
def push_tee(tcp: str, run: Callable) -> Generator[Popen, None, None]:
    """
    Run the PUSH socket with echoing to stdout.
    """
    yield from run(["zmq", "push", "--tee", "--bind", tcp])


# use a single connection for the lifetime of this class
class TestPushPull:
    @parametrize(
        "msg",
        (
            b"\n",
            b"foo\n",
            b"\x00\n",
        ),
    )
    def test_push_pull(self, msg: bytes, push: Popen, pull: Popen) -> None:
        """
        Push and pull newline-terminated messages over a single session.
        """
        # check for correct types
        assert isinstance(push.stdin, BufferedWriter)
        assert isinstance(pull.stdout, BufferedReader)

        # send
        push.stdin.write(msg)
        push.stdin.flush()

        # receive
        assert pull.stdout.readline() == msg


# use a new connection for every new parameter
@parametrize(
    "msg",
    (
        b"",
        b"foo",
        b"\x00",
    ),
)
def test_push_pull_eof(msg: bytes, push: Popen, pull: Popen) -> None:
    """
    Push and pull messages terminated via EOF from closing stdin.
    """
    # check for correct types
    assert isinstance(push.stdin, BufferedWriter)
    assert isinstance(pull.stdout, BufferedReader)

    # send
    push.stdin.write(msg)

    # close for signaling EOF and thereby make `read()` or `readline()` return
    push.stdin.close()

    # wait for receive, message printed with a newline appended
    assert pull.stdout.readline() == msg + b"\n"


# use a single connection for the lifetime of this class
class TestPushTee:
    @parametrize(
        "msg",
        (
            b"\n",
            b"foo\n",
            b"\x00\n",
        ),
    )
    def test_push_tee(self, msg: bytes, push_tee: Popen, pull: Popen) -> None:
        """
        Push and pull newline-terminated messages in a single session while
        also echoing the pushed messages to stdout on the pushing side.
        """
        # check for correct types
        assert isinstance(push_tee.stdin, BufferedWriter)
        assert isinstance(push_tee.stdout, BufferedReader)
        assert isinstance(pull.stdout, BufferedReader)

        # send
        push_tee.stdin.write(msg)
        push_tee.stdin.flush()

        # get echoed messages
        assert push_tee.stdout.readline() == msg

        # receive
        assert pull.stdout.readline() == msg


# use a new connection for every new parameter
@parametrize(
    "msg",
    (
        b"",
        b"foo",
        b"\x00",
    ),
)
def test_push_tee_eof(msg: bytes, push_tee: Popen, pull: Popen) -> None:
    """
    Push and pull messages terminated via EOF from closing stdin.
    Echo the pushed messages on the pushing side.
    """
    # check for correct types
    assert isinstance(push_tee.stdin, BufferedWriter)
    assert isinstance(push_tee.stdout, BufferedReader)
    assert isinstance(pull.stdout, BufferedReader)

    # send
    push_tee.stdin.write(msg)

    # close for signaling EOF and thereby ending the reading loop
    push_tee.stdin.close()

    # we echo the message with a newline appended
    assert push_tee.stdout.readline() == msg + b"\n"

    # wait for receive, message printed with a newline appended
    assert pull.stdout.readline() == msg + b"\n"


def test_interrupting_messages(push: Popen, pull: Popen) -> None:
    # create message of size ~128 MB,
    # much more than any default standard stream buffer
    msg = b"0123456789" * 2**24
    num = 3

    # type check
    assert isinstance(push.stdin, BufferedWriter)
    assert isinstance(push.stderr, BufferedReader)
    assert isinstance(pull.stdout, BufferedReader)
    assert isinstance(pull.stderr, BufferedReader)

    # send messages
    for _ in range(num):
        push.stdin.write(msg + b"\n")
        push.stdin.flush()

    # wait for the first message byte being written to stdout
    first = pull.stdout.read(1)

    # terminate immediately while data is in stdout buffer;
    # don't use the `stop` fixture here as the communication setup
    # leads to data loss
    push.terminate()
    pull.terminate()

    # get the rest of the messages
    rest = pull.stdout.readline()

    # get all received messages
    messages = [first + rest]
    for _ in range(num - 1):
        messages.append(pull.stdout.readline())

    # both process exited without issues
    for process in (push, pull):
        process.wait()
        assert process.returncode == 0

    # read the logs
    push_log = push.stderr.readlines()
    pull_log = pull.stderr.readlines()

    # ensure that we have put all messages in the push queue
    count = 0
    for line in push_log:
        if b"sent data via socket" in line:
            count += 1

    assert count == num

    # write out push and pull logs
    log = sorted(push_log + pull_log)
    sys.stderr.buffer.write(b"".join(log))
    sys.stderr.flush()

    # we received all data plus a newline character
    assert first == b"0"
    for o, out in enumerate(messages[:-1]):
        assert out == msg + b"\n"
        logger.debug(f"message {o + 1}/{num} passed")

    # on rare occasions, the last message has not been transmitted
    # before the previous message was fully written to stdout,
    # causing the pull command to exit - too early - since there
    # are no queued messages left to handle;
    # this is not considered to be a flaw of the pull command as it
    # cannot know how long it has to wait before new messages arrive
    if messages[-1]:
        assert messages[-1] == msg + b"\n"
        logger.debug(f"message {num}/{num} passed")
    else:  # pragma: no cover
        warn(
            (
                "last message was not transmitted before writing of "
                "previous message to stdout has finished."
            )
        )
