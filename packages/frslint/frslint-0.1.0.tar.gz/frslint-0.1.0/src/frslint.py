#!/usr/bin/env python3
"""
frslint - Linter and static analyzer for FreeSWITCH XML configuration files.
"""

import argparse
import sys

from analysis.FreeswitchAnalyzer import FreeswitchAnalyzer
from debug.DebugRunner import DebugRunner
from formatters import available_formats, get_analyze_formatter, get_lint_formatter
from lint.FreeswitchCodeStyleChecker import FreeswitchCodeStyleChecker


def cmd_analyze(args):
    """Run static analysis on configuration."""
    analyzer = FreeswitchAnalyzer(verbose=args.verbose)
    result = analyzer.analyze(args.file)

    formatter = get_analyze_formatter(args.format)
    formatter.print(result)

    sys.exit(1 if result.has_errors else 0)


def cmd_debug(args):
    """Debug the configuration."""
    runner = DebugRunner(file_path=args.file, verbose=args.verbose)
    channel_variables = {
        "destination_number": args.destination_number,
        "network_addr": args.network_addr,
    }
    runner.run(context_name=args.context_name, channel_variables=channel_variables)
    sys.exit(0)


def cmd_lint(args):
    """Check code style across all configuration files."""
    checker = FreeswitchCodeStyleChecker(
        indent_size=args.indent_size,
        max_line_length=args.max_line_length,
        max_consecutive_blank_lines=args.max_blank_lines,
        allow_tabs=args.allow_tabs,
        verbose=args.verbose,
    )
    result = checker.lint(args.file, fix=args.fix)

    formatter = get_lint_formatter(args.format)
    formatter.print(result, fix_mode=args.fix)

    sys.exit(1 if result.has_issues else 0)


def main():
    parser = argparse.ArgumentParser(
        prog="frslint",
        description="Linter and static analyzer for FreeSWITCH XML configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  frslint lint /etc/freeswitch/freeswitch.xml
  frslint lint /etc/freeswitch/freeswitch.xml --fix
  frslint lint /etc/freeswitch/freeswitch.xml --format json
  frslint analyze /etc/freeswitch/freeswitch.xml
  frslint analyze /etc/freeswitch/freeswitch.xml --format json
  frslint debug /etc/freeswitch/freeswitch.xml 1234
""",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # analyze command - static analysis
    p_analyze = subparsers.add_parser(
        "analyze", help="Static analysis: check for errors, undefined variables, invalid regex, etc."
    )
    p_analyze.add_argument("file", help="Path to freeswitch.xml")
    p_analyze.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    p_analyze.add_argument(
        "-f", "--format", choices=available_formats(), default="console", help="Output format (default: console)"
    )
    p_analyze.set_defaults(func=cmd_analyze)

    # debug command
    p_debug = subparsers.add_parser("debug", help="Debug dialplan execution")
    p_debug.add_argument("file", help="Path to freeswitch.xml")
    p_debug.add_argument("destination_number", help="Destination number to dial")
    p_debug.add_argument("-n", "--network-addr", help="Network address of the caller")
    p_debug.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    p_debug.add_argument("-c", "--context-name", default="public", help="Name of the context to run (default: public)")
    p_debug.set_defaults(func=cmd_debug)

    # lint command - code style checking
    p_lint = subparsers.add_parser("lint", aliases=["cs"], help="Check code style (indentation, whitespace, etc.)")
    p_lint.add_argument("file", help="Path to freeswitch.xml")
    p_lint.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    p_lint.add_argument(
        "-f", "--format", choices=available_formats(), default="console", help="Output format (default: console)"
    )
    p_lint.add_argument("--fix", action="store_true", help="Automatically fix fixable issues")
    p_lint.add_argument(
        "--indent-size", type=int, default=2, metavar="N", help="Expected indentation size in spaces (default: 2)"
    )
    p_lint.add_argument(
        "--max-line-length", type=int, default=120, metavar="N", help="Maximum allowed line length (default: 120)"
    )
    p_lint.add_argument(
        "--max-blank-lines",
        type=int,
        default=2,
        metavar="N",
        help="Maximum consecutive blank lines allowed (default: 2)",
    )
    p_lint.add_argument("--allow-tabs", action="store_true", help="Allow tab characters for indentation")
    p_lint.set_defaults(func=cmd_lint)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
