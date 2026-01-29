#!/usr/bin/env python
"""Fast CLI entry point that checks for --version before loading heavy modules."""
# this_file: src/abersetz/cli_fast.py

import sys


def handle_version() -> None:
    """Handle --version flag with minimal imports."""
    if "--version" in sys.argv or "version" in sys.argv:
        # Only import version, nothing else
        from importlib import metadata

        try:
            version = metadata.version("abersetz")
        except metadata.PackageNotFoundError:
            from .__about__ import __version__ as version  # type: ignore

        print(f"abersetz version {version}")
        sys.exit(0)


def main() -> None:
    """Fast CLI entry point that defers heavy imports."""
    # Check for version flag first with minimal imports
    handle_version()

    # Now load the full CLI only if needed
    from .cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
