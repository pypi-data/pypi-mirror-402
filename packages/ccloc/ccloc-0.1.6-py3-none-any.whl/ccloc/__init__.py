"""Count Lines of Code CLI Tool"""

from ccloc.cli import cli as _cli


def main() -> None:
    # Use Click's Command.main to avoid Pylint E1120 on parameterless call
    _cli.main(standalone_mode=True)
