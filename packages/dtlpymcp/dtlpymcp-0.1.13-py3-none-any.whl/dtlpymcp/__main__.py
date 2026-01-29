"""
CLI entry point for dtlpymcp.
Reads from STDIN and writes to STDOUT.
"""

import sys
import argparse
from dtlpymcp.proxy import main as proxy_main


def main():
    parser = argparse.ArgumentParser(description="Dataloop MCP Proxy Server CLI")
    subparsers = parser.add_subparsers(dest="command", required=False)

    # 'start' subcommand
    start_parser = subparsers.add_parser("start", help="Start the MCP proxy server (STDIO mode)")
    start_parser.add_argument(
        "--sources-file", "-s", type=str, default=None, help="Path to a JSON file with MCP sources to load"
    )
    start_parser.add_argument(
        "--init-timeout",
        "-t",
        type=float,
        default=30.0,
        help="Timeout in seconds for Dataloop context initialization (default: 30.0)",
    )
    start_parser.add_argument(
        "--log-level",
        "-l",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    if args.command == "start":
        sys.exit(proxy_main(sources_file=args.sources_file, init_timeout=args.init_timeout, log_level=args.log_level))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    main()
