#!/usr/bin/env python3
"""
SpaceTimePy Web Explorer

A web-based interface for exploring SpaceTimePy databases.
"""

import argparse
import logging

from spacetimepy.interface.mcp.api.controller import run_mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_explorer(
    db_file: str,
    api_host: str = "127.0.0.1",
    api_port: int = 3002,
) -> None:
    """Run the web explorer.

    Args:
        db_file: Path to the SQLite database file
        api_host: Host to run the API server on
        api_port: Port to run the API server on
        debug: Whether to run in debug mode
    """


    run_mcp(db_file, api_host, api_port)


def main():
    """Main function for the explorer command line tool."""
    parser = argparse.ArgumentParser(description="SpaceTimePy Web Explorer")
    parser.add_argument("db_file", help="Path to the SQLite database file")
    parser.add_argument(
        "--api-host", default="127.0.0.1", help="Host to run the API server on"
    )
    parser.add_argument(
        "--api-port", type=int, default=3002, help="Port to run the API server on"
    )

    args = parser.parse_args()
    run_explorer(
        args.db_file,
        args.api_host,
        args.api_port,
    )


if __name__ == "__main__":
    main()
