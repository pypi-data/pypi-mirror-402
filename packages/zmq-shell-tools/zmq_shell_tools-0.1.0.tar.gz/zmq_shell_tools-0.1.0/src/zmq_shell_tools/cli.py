import sys
from contextlib import AbstractContextManager, ExitStack
from functools import wraps
from types import TracebackType
from typing import Any, Callable, Sequence, override

from click import ClickException, Context, Group, Path, option
from loguru import logger
from zmq import Context as ZMQContext
from zmq import Socket, SocketOption, SocketType, ZMQError
from zmq.asyncio import Context as AsyncZMQContext
from zmq.constants import _OptType


class OrderedGroup(Group):
    """
    OrderedGroup is a subclass of [`click.Group`][click.Group] that maintains
    the order of subcommands.
    """

    @override
    def list_commands(self, ctx: Context) -> list[str]:
        """
        Returns a list of subcommand names in the order they should appear.

        Arguments:
            ctx: the `click.Context` of the current command invokation.

        Returns:
            a list of command names in read order.
        """
        return list(self.commands)


#
# logging
#

LEVEL = (
    # 50
    "CRITICAL",
    # 40
    "ERROR",
    # 30
    "WARNING",
    # 25
    "SUCCESS",
    # 20
    "INFO",
    # 10
    "DEBUG",
    # 5
    "TRACE",
)
"""Loguru log level ordered by severity."""

verbose: Callable = option(
    "--verbose",
    "-v",
    "verbose",
    help="Set the logging level. Can be given multiple times.",
    count=True,
)
"""The `--verbose` option for a `zmq` command."""


debug: Callable = option(
    "--debug",
    "-d",
    "debug",
    help=(
        "Set the logging level to DEBUG, being equivalent to "
        f"-{'v' * (LEVEL.index('DEBUG') + 1)}."
    ),
    is_flag=True,
)
"""The `--debug` option for a `zmq` command."""


logfile: Callable = option(
    "--log",
    "-l",
    "log",
    help="Path to a log file.",
    type=Path(exists=False, dir_okay=False, file_okay=True),
)
"""The `--log` option for a `zmq` command."""


def log(verbose: int, file: str | None = None) -> int | None:
    """
    Potentially add a logging handler based on verbosity.

    Arguments:
        verbose: the verbosity or severity level.
        file: the path to a log file.
    """
    if verbose == 0:
        # verbose flag was not given
        return

    # cap the count to the length of available level
    verbose = min(verbose, len(LEVEL)) - 1
    level = LEVEL[verbose]

    # set the sink
    # sink = file or (lambda msg: sys.stderr.write(msg))
    sink = file or sys.stderr

    # add the logging handler
    handler = logger.add(sink, level=level)

    logger.info(f"set log level to {level}")

    return handler


#
# socket
#

options: Callable = option(
    "--option",
    "-o",
    "options",
    metavar="OPTION VALUE",
    help="Set a socket option to a certain value. Can be given multiple times.",
    multiple=True,
    nargs=2,
)
"""The socket `--option` options for a `zmq` command."""


bind: Callable = option(
    "--bind",
    "-b",
    "bind",
    metavar="ADDRESS",
    help="Bind to the given address. Can be given multiple times.",
    multiple=True,
)
"""The `--bind` options for a `zmq` command."""


connect: Callable = option(
    "--connect",
    "-c",
    "connect",
    metavar="ADDRESS",
    help="Connect to the given address. Can be given multiple times.",
    multiple=True,
)
"""The `--connect` options for a `zmq` command."""


def apply(socket: Socket, options: Sequence[tuple[str, str]]) -> None:
    """
    Apply socket options given by the CLI.

    Arguments:
        socket: the socket to set options on.
        options: pairs of option names and values to apply.

    Raises:
        ClickException: when the option name is invalid, the option value
            cannot be parsed or the option is invalid for the given socket.
    """
    # specify parsers for the attached option types
    PARSERS = {
        _OptType.int: int,
        _OptType.int64: int,
        _OptType.bytes: lambda value: value.encode(),
    }

    if options:
        logger.debug("applying options")

    for name, value in options:
        # ensure correct option name spelling
        name = name.upper()

        # check whether this option exists
        try:
            option = SocketOption[name]
        except KeyError:
            raise ClickException(f"No such socket option '{name}'")

        # get the parser corresponding to the attached option type
        type = option._opt_type

        try:
            parse = PARSERS[type]
        except KeyError:
            raise ClickException(f"Socket option '{name}': not considered to be parsed")

        # parse the given value
        try:
            value = parse(value)
        except ValueError:
            raise ClickException(
                f"Socket option '{name}': cannot convert value to {type}"
            )

        # check whether this name-value combination can be set as an option
        try:
            socket.set(option, value)
        except ZMQError as exc:
            raise ClickException(f"Socket option '{name}': {exc}")

        logger.debug(f"applied option {name} = {value}")

    if options:
        logger.debug("applied options")


def check(addresses: Sequence[str]) -> None:
    """
    Check the passed addresses to bind or connect to.

    Arguments:
        addresses: the addresses to check.

    Raises:
        ClickException: when the sequence of addresses is empty.
    """
    logger.debug("checking addresses")

    if not addresses:
        raise ClickException("No address specified.")

    logger.debug("checked addresses")


#
# common
#


class ExitLog(AbstractContextManager):
    """
    A Context Manager simply writing an exit log message.
    """

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        """
        Hook executed on leaving the context.

        It logs an exit message to the `INFO` level.

        Arguments:
            exc_type: the exception class.
            exc_value: the instance of the exception class.
            exc_tb: the traceback of the instance of the exception class.
        """
        logger.info("exiting")


def socket(type: SocketType | int, sync: bool = True) -> Callable:
    """
    Configure a decorator injecting a ZMQ socket which is automatically
    closed.

    Arguments:
        type: the ZMQ socket type.
        sync: inject a synchronous socket if `True`, else an asynchronous one.

    Returns:
        the configured decorator.
    """
    # ensure type to be a member of `SocketType`
    type = SocketType(type)

    def _socket(cmd: Callable) -> Callable:
        """
        Decorator for a command for proper socket initialization,
        configuration and context management of the socket context,
        the socket itself as well as socket bindings and connections.

        It also injects the socket instance as a keyword argument into
        the command.

        Arguments:
            cmd: the command to inject the socket instance into.

        Returns:
            the wrapped command after which the injected socket is
            automatically closed.
        """

        @verbose
        @debug
        @logfile
        @options
        @bind
        @connect
        @wraps(cmd)
        def managed(*args: Any, **kwargs: Any) -> None:
            """
            Wrapper around a command for proper socket initialization,
            configuration and context management of the socket context,
            the socket itself as well as socket bindings and connections.

            It also injects the socket instance as a keyword argument into
            the command.

            Arguments:
                *args: positional arguments passed to the wrapped command.
                **kwargs: keyword arguments passed to the wrapped command.

            Raises:
                ClickException: on wrong or missing CLI arguments.
            """
            # setup logging
            verbose = kwargs["verbose"]
            debug = kwargs["debug"]
            logfile = kwargs["log"]

            if debug:
                verbose += LEVEL.index("DEBUG") + 1

            handler = log(verbose, file=logfile)

            # get a socket instance
            ctx = ZMQContext() if sync else AsyncZMQContext()
            socket = ctx.socket(type)

            # get and apply socket options
            options = kwargs["options"]

            apply(socket, options)

            # get and check addresses
            bind = kwargs["bind"]
            connect = kwargs["connect"]

            check(bind + connect)

            # ensure to exit the context, the socket as well as all bindings
            # and connections properly after the command has returned
            with ExitLog(), ctx, socket, ExitStack() as stack:
                try:
                    # bind to the given addresses
                    for address in bind:
                        stack.enter_context(socket.bind(address))
                        logger.debug(f"bound to address {address}")

                    # connect to the given addresses
                    for address in connect:
                        stack.enter_context(socket.connect(address))
                        logger.debug(f"connected to address {address}")
                except ZMQError as exc:
                    raise ClickException(str(exc))

                logger.info(f"running {type.name} socket")

                # run the command with the socket instance injected
                cmd(*args, socket=socket, **kwargs)

            # proper cleanup for sequential use
            logger.remove(handler)

        return managed

    return _socket
