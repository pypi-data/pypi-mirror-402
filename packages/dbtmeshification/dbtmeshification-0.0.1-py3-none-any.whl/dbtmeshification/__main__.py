"""
Entry point for the dbtmeshification CLI.
"""
from dbtmeshification.cli import cli


def main():
    inputs = cli()

    if hasattr(inputs, "func"):
        exit_code = inputs.func(inputs)
        exit(exit_code if exit_code is not None else 0)


if __name__ == "__main__":
    main()
