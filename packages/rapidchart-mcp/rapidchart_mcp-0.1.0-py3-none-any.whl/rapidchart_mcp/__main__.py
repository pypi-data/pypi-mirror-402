"""CLI entry point."""
import asyncio
import sys
from .server import main


def cli():
    """CLI entry point"""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    cli()

