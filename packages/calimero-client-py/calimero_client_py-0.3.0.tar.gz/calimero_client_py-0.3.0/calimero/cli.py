"""
Command Line Interface for Calimero Client Python Library.
"""

import argparse
import asyncio
import sys
from typing import Optional

from calimero_client_py import create_connection, create_client, AuthMode


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calimero Client Python Library CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  calimero-client-py --help
  calimero-client-py --version
  calimero-client-py --base-url https://test.merod.dev.p2p.aws.calimero.network list-contexts
        """,
    )

    parser.add_argument(
        "--version", action="version", version="calimero-client-py 0.3.0"
    )

    parser.add_argument(
        "--base-url",
        default="https://test.merod.dev.p2p.aws.calimero.network",
        help="Base URL for the Calimero server (default: https://test.merod.dev.p2p.aws.calimero.network)",
    )

    parser.add_argument(
        "--auth-mode",
        choices=["none", "required"],
        default="none",
        help="Authentication mode (default: none)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List contexts command
    list_parser = subparsers.add_parser("list-contexts", help="List all contexts")

    # Add more commands here as needed

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create connection
    connection = create_connection(api_url=args.base_url, node_name=None)

    # Create client
    client = create_client(connection)

    # Execute command
    if args.command == "list-contexts":
        try:
            contexts = client.list_contexts()
            print(f"Found {contexts} contexts:")
        except Exception as e:
            print(f"Error listing contexts: {e}", file=sys.stderr)
            sys.exit(1)


def cli():
    """CLI entry point function."""
    main()


if __name__ == "__main__":
    cli()
