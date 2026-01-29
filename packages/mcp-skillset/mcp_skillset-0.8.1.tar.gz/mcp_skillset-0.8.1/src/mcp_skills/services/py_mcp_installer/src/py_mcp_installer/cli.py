"""Command-line interface for py-mcp-installer.

This module provides CLI commands for managing MCP server installations,
including the doctor diagnostic command.

Usage:
    py-mcp-installer doctor [--full] [--server NAME] [--json] [--verbose]
    py-mcp-installer --version
    py-mcp-installer --help

Example:
    # Quick diagnostics (fast)
    $ py-mcp-installer doctor

    # Full diagnostics with server tests
    $ py-mcp-installer doctor --full

    # Test specific server
    $ py-mcp-installer doctor --server mcp-ticketer --full

    # JSON output for programmatic use
    $ py-mcp-installer doctor --json
"""

import argparse
import json
import sys
from typing import NoReturn

from . import __version__
from .exceptions import PlatformDetectionError
from .mcp_doctor import DiagnosticIssue, DiagnosticReport, MCPDoctor
from .platform_detector import PlatformDetector
from .types import DiagnosticStatus, ServerDiagnostic, ServerStatus


def main() -> NoReturn:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="py-mcp-installer",
        description="Universal MCP server installer for AI coding tools",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Doctor command
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Run diagnostics on MCP installation",
        description=(
            "Run comprehensive diagnostics on your MCP server installation. "
            "By default runs quick checks on configuration and commands. "
            "Use --full to also test server protocol compliance."
        ),
    )
    doctor_parser.add_argument(
        "--full",
        action="store_true",
        help="Run full diagnostics including server protocol tests (slower)",
    )
    doctor_parser.add_argument(
        "--server",
        type=str,
        help="Test specific server only",
        metavar="NAME",
    )
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    doctor_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    doctor_parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout for server tests in seconds (default: 10)",
        metavar="SECONDS",
    )

    args = parser.parse_args()

    if args.command == "doctor":
        exit_code = cmd_doctor(args)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(0)


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run doctor diagnostics command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for issues found, 2 for errors)
    """
    try:
        # Detect platform
        detector = PlatformDetector()
        platform_info = detector.detect()

        # Create doctor
        doctor = MCPDoctor(
            platform_info,
            timeout=args.timeout,
            verbose=args.verbose,
        )

        # Run diagnostics
        report = doctor.diagnose(full=args.full)

        # Filter to specific server if requested
        if args.server:
            report = _filter_report_by_server(report, args.server)

        # Output results
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            _print_report(report, verbose=args.verbose)

        # Return appropriate exit code
        if report.status == DiagnosticStatus.CRITICAL:
            return 1
        elif report.status == DiagnosticStatus.DEGRADED:
            return 0  # Warnings don't fail
        else:
            return 0

    except PlatformDetectionError as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"\n{_color('red', 'ERROR')}: {e}")
            print(f"\n{e.recovery_suggestion}")
        return 2

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"\n{_color('red', 'ERROR')}: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
        return 2


def _filter_report_by_server(
    report: DiagnosticReport, server_name: str
) -> DiagnosticReport:
    """Filter report to only include issues for specific server.

    Args:
        report: Full diagnostic report
        server_name: Server name to filter by

    Returns:
        Filtered report with only specified server's issues
    """
    from dataclasses import replace

    filtered_issues = [
        issue
        for issue in report.issues
        if issue.server_name == server_name or issue.server_name is None
    ]

    filtered_server_reports = {
        name: diag
        for name, diag in report.server_reports.items()
        if name == server_name
    }

    # Recalculate status based on filtered issues
    if any(i.severity == "critical" for i in filtered_issues):
        status = DiagnosticStatus.CRITICAL
    elif any(i.severity == "warning" for i in filtered_issues):
        status = DiagnosticStatus.DEGRADED
    else:
        status = DiagnosticStatus.HEALTHY

    return replace(
        report,
        issues=filtered_issues,
        server_reports=filtered_server_reports,
        status=status,
    )


def _print_report(report: DiagnosticReport, verbose: bool = False) -> None:
    """Print diagnostic report in human-readable format.

    Args:
        report: Diagnostic report to print
        verbose: Enable verbose output
    """
    # Header
    print("\n" + "=" * 50)
    print("MCP Installation Diagnostics")
    print("=" * 50)

    # Platform info
    print(f"\nPlatform: {report.platform.value}")

    # Status with color
    status_colors = {
        DiagnosticStatus.HEALTHY: "green",
        DiagnosticStatus.DEGRADED: "yellow",
        DiagnosticStatus.CRITICAL: "red",
    }
    status_symbols = {
        DiagnosticStatus.HEALTHY: "\u2705",
        DiagnosticStatus.DEGRADED: "\u26a0\ufe0f ",
        DiagnosticStatus.CRITICAL: "\u274c",
    }
    status_color = status_colors.get(report.status, "white")
    status_symbol = status_symbols.get(report.status, "")
    print(
        f"Status: {status_symbol} "
        f"{_color(status_color, report.status.value.upper())}"
    )

    # Check counts
    print(f"Checks: {report.checks_passed}/{report.checks_total} passed")

    # Critical issues
    critical_issues = [i for i in report.issues if i.severity == "critical"]
    if critical_issues:
        print(f"\n{_color('red', 'CRITICAL Issues:')}")
        for issue in critical_issues:
            _print_issue(issue)

    # Warning issues
    warning_issues = [i for i in report.issues if i.severity == "warning"]
    if warning_issues:
        print(f"\n{_color('yellow', 'WARNING Issues:')}")
        for issue in warning_issues:
            _print_issue(issue)

    # Info issues (verbose only)
    if verbose:
        info_issues = [i for i in report.issues if i.severity == "info"]
        if info_issues:
            print(f"\n{_color('blue', 'INFO:')}")
            for issue in info_issues:
                _print_issue(issue)

    # Server status
    if report.server_reports:
        print(f"\n{_color('cyan', 'Server Status:')}")
        for name, diag in report.server_reports.items():
            _print_server_status(diag)

    # Recommendations
    if report.recommendations:
        print(f"\n{_color('cyan', 'Recommendations:')}")
        for rec in report.recommendations:
            print(f"  \u2022 {rec}")

    print()  # Final newline


def _print_issue(issue: DiagnosticIssue) -> None:
    """Print a single diagnostic issue.

    Args:
        issue: Issue to print
    """
    server_info = f" ({issue.server_name})" if issue.server_name else ""
    print(f"  [{issue.category.value.upper()}]{server_info}: {issue.message}")
    print(f"    Fix: {issue.fix_suggestion}")


def _print_server_status(diag: "ServerDiagnostic") -> None:
    """Print server diagnostic status.

    Args:
        diag: Server diagnostic to print
    """

    status_colors = {
        ServerStatus.HEALTHY: "green",
        ServerStatus.UNREACHABLE: "red",
        ServerStatus.ERROR: "yellow",
        ServerStatus.UNKNOWN: "gray",
    }
    status_symbols = {
        ServerStatus.HEALTHY: "\u2705",
        ServerStatus.UNREACHABLE: "\u274c",
        ServerStatus.ERROR: "\u26a0\ufe0f ",
        ServerStatus.UNKNOWN: "\u2753",
    }

    color = status_colors.get(diag.status, "white")
    symbol = status_symbols.get(diag.status, "")

    status_str = f"{symbol} {_color(color, diag.status.value.upper())}"

    if diag.status == ServerStatus.HEALTHY:
        details = (
            f"(tools: {diag.tool_count}, "
            f"resources: {diag.resource_count}, "
            f"prompts: {diag.prompt_count})"
        )
        if diag.response_time_ms:
            details += f" - {diag.response_time_ms:.0f}ms"
        print(f"  {diag.name}: {status_str} {details}")
    elif diag.error:
        print(f"  {diag.name}: {status_str} - {diag.error}")
    else:
        print(f"  {diag.name}: {status_str}")


def _color(color: str, text: str) -> str:
    """Apply ANSI color to text if terminal supports it.

    Args:
        color: Color name (red, green, yellow, blue, cyan, gray)
        text: Text to colorize

    Returns:
        Colorized text string
    """
    # Check if stdout is a tty
    if not sys.stdout.isatty():
        return text

    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "gray": "\033[90m",
        "white": "\033[97m",
    }

    reset = "\033[0m"
    color_code = colors.get(color, "")

    return f"{color_code}{text}{reset}"


if __name__ == "__main__":
    main()
