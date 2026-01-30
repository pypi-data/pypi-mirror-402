from itertools import permutations
from pathlib import Path
from typing import Any, cast

from click import Command, Context, command, group
from click.exceptions import ClickException
from click.testing import CliRunner
from loguru import logger
from pytest import mark, raises
from zmq import SocketType

from zmq_shell_tools.cli import OrderedGroup, socket

parametrize = mark.parametrize


#
# main help page
#


def cmd(name: str | None = None) -> Command:
    """
    Get a dummy command.

    Arguments:
        name: the name for the command.

    Returns:
        a dummy command which does nothing.
    """

    @command(name)
    def _cmd(): ...

    return _cmd


@parametrize(
    "cmds",
    permutations((cmd("a"), cmd("b"), cmd("c"))),
)
def test_ordered_commands(cmds: tuple[Command]) -> None:
    """
    Subcommands are listed as defined in code, not alphabetically.
    """

    # define a test command group with subcommands
    @group(cls=OrderedGroup)
    def main(): ...

    for cmd in cmds:
        main.add_command(cmd)

    # save names and declare type
    names = cast(list[str], [cmd.name for cmd in cmds])

    # create a dummy context
    dummy = Context(main)

    # the listed commands are in the same order as defined
    assert main.list_commands(dummy) == names

    # generate help message
    runner = CliRunner()
    res = runner.invoke(main)

    # strip spaces from the output
    output = "\n".join(line.strip(" ") for line in res.output.splitlines())

    # the commands are listed in the help message in the same order as defined
    assert "\n".join(names) in output


@command
@socket(SocketType.ROUTER)
def socket_cmd(*args: Any, **kwargs: Any) -> None:
    """
    A command logging messages at different severity levels.

    Arguments:
        *args: positional arguments from the socket setup.
        **kwargs: keyword arguments from the socket setup.
    """
    logger.critical("critical")
    logger.error("error")
    logger.warning("warning")
    logger.success("success")
    logger.info("info")
    logger.debug("debug")
    logger.trace("trace")


def make_context(cmd: Command, args: list[str]) -> Context:
    """
    Get the context for a command with given CLI arguments.

    Arguments:
        cmd: the command to get the context for.
        args: the CLI arguments being parsed for the context.
    """
    return cmd.make_context(cmd.name, args)


LEVELS = {
    "critical",
    "error",
    "warning",
    "success",
    "info",
    "debug",
    "trace",
}
"""Present logging levels."""


@parametrize(
    "to_file",
    (
        False,
        True,
    ),
    ids=(
        "stderr",
        "file",
    ),
)
@parametrize(
    ("args", "expected_levels"),
    (
        # no logging
        (
            tuple(),
            set(),
        ),
        # only critical log messages
        (
            ("-v",),
            {
                "critical",
            },
        ),
        # critical and error log messages
        (
            ("-vv",),
            {
                "critical",
                "error",
            },
        ),
        # critical, error and warning log messages
        (
            ("-vvv",),
            {
                "critical",
                "error",
                "warning",
            },
        ),
        # critical, error, warning and success log messages
        (
            ("-vvvv",),
            {
                "critical",
                "error",
                "warning",
                "success",
            },
        ),
        # critical, error, warning, success and info log messages
        (
            ("-vvvvv",),
            {
                "critical",
                "error",
                "warning",
                "success",
                "info",
            },
        ),
        # critical, error, warning, success, info and debug log messages
        (
            ("-vvvvvv",),
            {
                "critical",
                "error",
                "warning",
                "success",
                "info",
                "debug",
            },
        ),
        # all log messages
        (
            ("-vvvvvvv",),
            LEVELS,
        ),
        # all log messages, too many verbose flags given
        (
            ("-vvvvvvvv",),
            LEVELS,
        ),
        # all log messages, way too many verbose flags given
        (
            (f"-{'v' * 20}",),
            LEVELS,
        ),
        # debug shortcut verbose flag, all but trace log messages
        (
            ("--debug",),
            {
                "critical",
                "error",
                "warning",
                "success",
                "info",
                "debug",
            },
        ),
        # debug shortcut flag plus verbose flag, all log messages
        (
            ("--debug", "-v"),
            LEVELS,
        ),
        # debug shortcut flag way more verbose flags, all log messages
        (
            ("--debug", "-vvvvvvv"),
            LEVELS,
        ),
    ),
    ids=lambda val: "-".join(val) if not isinstance(val, set) else "",
)
def test_logging(
    capteesys,
    tmp_path: Path,
    to_file: bool,
    args: tuple[str, ...],
    expected_levels: set[str],
) -> None:
    """
    Logging messages appear at given verbosity and in the right place.
    """
    # logging is basically enabled
    verbose = len(args) > 0

    # define the logfile path
    if to_file and verbose:
        log = tmp_path / "test.log"
        args += ("--log", str(log))

    # satisfy address constraint
    args += ("--bind", "inproc://dummy")

    # run the logging command
    socket_cmd(args, standalone_mode=False)

    if to_file and verbose:
        # read the automatically created logfile
        with log.open("r") as fd:
            lines = fd.read().splitlines()
    else:
        # read the captured standard streams
        captured = capteesys.readouterr()
        lines = captured.err.splitlines()

    # for every expected level, there is exactly one message
    for expected_level in expected_levels:
        assert sum([line.endswith(expected_level) for line in lines]) == 1

    # for every not expected level, there is not a single message
    for not_expected_level in LEVELS - expected_levels:
        assert all([not line.endswith(not_expected_level) for line in lines])


#
# options
#


@parametrize(
    "args",
    (
        # invalid option name
        ["--option", "blub", "no such option"],
        # option value not parsable
        ["--option", "linger", "expected integer"],
        # option not applicable to socket type
        ["--option", "hiccup_msg", "not for ROUTER socket"],
        # not considered to be parsable,
        ["--option", "fd", "1000"],
    ),
)
def test_wrong_options(args: list[str]) -> None:
    """
    Not applicable options abort the command.
    """
    ctx = make_context(socket_cmd, args)
    with raises(ClickException):
        socket_cmd.invoke(ctx)


@parametrize(
    ("args", "expected_args"),
    (
        # no options
        (
            [],
            tuple(),
        ),
        # single option
        (
            [
                "--option",
                "sndhwm",
                "10",
            ],
            (("sndhwm", "10"),),
        ),
        # multiple options
        (
            [
                "--option",
                "sndhwm",
                "10",
                "--option",
                "rcvhwm",
                "5",
            ],
            (
                ("sndhwm", "10"),
                ("rcvhwm", "5"),
            ),
        ),
    ),
)
def test_parsing_options(args: list[str], expected_args: tuple[tuple[str]]) -> None:
    """
    Socket options can be given as CLI options with two sequential values
    and the option's values are correctly translated to the respective type.
    """
    # satisfy address constraint
    args += ["--bind", "inproc://dummy"]

    # parse arguments
    ctx = make_context(socket_cmd, args)
    assert ctx.params["options"] == expected_args

    # apply options, no error
    socket_cmd.invoke(ctx)


#
# addresses
#


@parametrize(
    "args",
    (
        # no addresses
        [],
        # invalid address
        ["--bind", "tcp://localhost:"],
        # permission denied
        ["--bind", "tcp://localhost:1"],
    ),
)
def test_parsing_wrong_addresses(args) -> None:
    """
    Running a socket without any addresses specified is pointless.
    """
    # bypass specifying standalone mode
    ctx = make_context(socket_cmd, args)

    # run the address check
    with raises(ClickException):
        socket_cmd.invoke(ctx)


@parametrize(
    ("args", "expected_args"),
    (
        # single `--bind`
        (
            [
                "--bind",
                "inproc://test",
            ],
            {
                "bind": ("inproc://test",),
                "connect": tuple(),
            },
        ),
        # single `--connect`
        (
            [
                "--connect",
                "inproc://test",
            ],
            {
                "bind": tuple(),
                "connect": ("inproc://test",),
            },
        ),
        # single `--bind` and single `--connect`
        (
            [
                "--bind",
                "inproc://bind",
                "--connect",
                "inproc://connect",
            ],
            {
                "bind": ("inproc://bind",),
                "connect": ("inproc://connect",),
            },
        ),
        # multiple `--bind`s
        (
            [
                "--bind",
                "inproc://foo",
                "--bind",
                "inproc://bar",
                "--bind",
                "inproc://baz",
            ],
            {
                "bind": (
                    "inproc://foo",
                    "inproc://bar",
                    "inproc://baz",
                ),
                "connect": tuple(),
            },
        ),
        # multiple `--connect`s
        (
            [
                "--connect",
                "inproc://foo",
                "--connect",
                "inproc://bar",
                "--connect",
                "inproc://baz",
            ],
            {
                "bind": tuple(),
                "connect": (
                    "inproc://foo",
                    "inproc://bar",
                    "inproc://baz",
                ),
            },
        ),
        # multiple `--bind`s and `--connect`s
        (
            [
                "--bind",
                "inproc://foo",
                "--bind",
                "inproc://bar",
                "--bind",
                "inproc://baz",
                "--connect",
                "inproc://quux",
                "--connect",
                "inproc://quib",
                "--connect",
                "inproc://quam",
            ],
            {
                "bind": (
                    "inproc://foo",
                    "inproc://bar",
                    "inproc://baz",
                ),
                "connect": (
                    "inproc://quux",
                    "inproc://quib",
                    "inproc://quam",
                ),
            },
        ),
    ),
)
def test_parsing_addresses(
    args: list[str], expected_args: dict[str, tuple[str]]
) -> None:
    """
    Sockets (except for PAIR and CHANNEL) allow binding and connecting
    to multiple addresses simultaneously.
    """
    # parse arguments
    ctx = make_context(socket_cmd, args)

    # the addresses are parsed in the correct way
    for name, value in expected_args.items():
        assert ctx.params[name] == value

    # run check and apply addresses to the socket
    socket_cmd.invoke(ctx)
