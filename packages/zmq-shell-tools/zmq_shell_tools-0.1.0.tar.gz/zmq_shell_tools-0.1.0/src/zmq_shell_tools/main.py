import sys
from typing import Any

from click import group, option, version_option
from loguru import logger
from zmq import DONTWAIT, PULL, PUSH, Socket, select

from .cli import OrderedGroup, socket
from .signal import Shield, interruptable

# make the process interruptable
interruptable()


@group(cls=OrderedGroup)
@version_option(message="%(version)s")
def zmq() -> None:
    """
    ZMQ sockets for the command line.
    """
    logger.remove(0)


@zmq.command
@option(
    "--tee",
    "-t",
    help="Also echo to STDOUT.",
    is_flag=True,
)
@socket(PUSH)
def push(socket: Socket, tee: bool, **params: Any) -> None:
    """
    Push input from STDIN to ADDRESS.
    \f

    Arguments:
        socket: the injected `PUSH` socket instance.
        tee: if `True`, echo to `sys.stdout`, else remain silent.
        **params: the parameters from the ZMQ socket setup.
    """
    _i = sys.stdin.buffer
    _o = sys.stdout.buffer

    logger.info("listening for data on stdin")

    # always send the very first data, which might be empty signaling EOF
    first = True

    while True:
        select([_i], [], [], None)

        with Shield():
            data = _i.readline()

            if not first and not data:
                logger.debug("received EOF on stdin")
                break

            while True:
                logger.debug("received data on stdin")

                stripped = data.rstrip(b"\n").split(b"\x00")
                socket.send_multipart(stripped)
                logger.debug("sent data via socket")

                if tee:
                    # possible EOF instead of newline
                    if not data.endswith(b"\n"):
                        data += b"\n"

                    _o.write(data)
                    _o.flush()

                    logger.debug("wrote data to stdout")

                # poll the stdin buffer
                if select([_i], [], [], 0)[0]:
                    data = _i.readline()
                else:
                    logger.debug("no buffered data")
                    break

            first = False


@zmq.command
@socket(PULL)
def pull(socket: Socket, **params: Any) -> None:
    """
    Pull messages from ADDRESS and print them to STDOUT.
    \f

    Arguments:
        socket: the injected `PULL` socket instance.
        **params: the parameters from the ZMQ socket setup.
    """
    _o = sys.stdout.buffer

    while True:
        # wait for new messages
        logger.info("listening for data on socket")
        select([socket], [], [], None)

        with Shield():
            data = socket.recv_multipart(flags=DONTWAIT)

            while True:
                logger.debug("received data on socket")

                data = b"\x00".join(data) + b"\n"

                _o.write(data)
                _o.flush()
                logger.debug("wrote data to stdout")

                # poll the local message queue
                if select([socket], [], [], 0)[0]:
                    data = socket.recv_multipart(flags=DONTWAIT)
                else:
                    logger.debug("no queued data")
                    break
