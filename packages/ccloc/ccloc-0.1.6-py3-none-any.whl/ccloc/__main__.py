"""Module entry point to support `python -m ccloc`."""

from ccloc.cli import cli as _cli


def main() -> None:
    # Use Click's Command.main to avoid linter false positives
    _cli.main(standalone_mode=True)


if __name__ == "__main__":
    main()
