"""Entry point for running the IP Query MCP server."""

import asyncio
from .server import serve


def main():
    """Main entry point for the package."""
    asyncio.run(serve())


if __name__ == "__main__":
    main()
