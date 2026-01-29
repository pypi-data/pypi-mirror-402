"""MCP Doctor for comprehensive installation diagnostics.

This module provides diagnostic capabilities for MCP server installations,
including configuration validation, command accessibility checks, environment
variable verification, and JSON-RPC protocol compliance testing.

Design Philosophy:
- Quick mode for fast config/command checks (default)
- Full mode for complete protocol compliance testing
- Clear severity levels (critical, warning, info)
- Actionable fix suggestions for all issues
- Reuse patterns from MCPInspector

Example:
    >>> from py_mcp_installer import MCPDoctor, PlatformDetector
    >>> detector = PlatformDetector()
    >>> info = detector.detect()
    >>> doctor = MCPDoctor(info)
    >>> report = doctor.diagnose(full=False)
    >>> print(report.summary())
    >>> if report.status == DiagnosticStatus.CRITICAL:
    ...     for issue in report.issues:
    ...         print(f"{issue.severity}: {issue.message}")
"""

import json
import logging
import select
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .config_manager import ConfigManager
from .exceptions import ConfigurationError
from .types import (
    ConfigFormat,
    DiagnosticCategory,
    DiagnosticStatus,
    MCPServerConfig,
    Platform,
    PlatformInfo,
    ServerStatus,
)
from .utils import resolve_command_path

logger = logging.getLogger(__name__)

# ============================================================================
# Data Classes
# ============================================================================


@dataclass(frozen=True)
class DiagnosticIssue:
    """Represents a single diagnostic issue.

    Attributes:
        category: Type of issue (config, server, command, environment, platform)
        severity: Issue severity level
            - critical: Prevents server from working
            - warning: May cause problems
            - info: Recommendations only
        check_name: Name of the check that found this issue (e.g., "config_exists")
        message: Human-readable issue description
        server_name: Affected server name (None for global issues)
        fix_suggestion: How to fix this issue
        details: Additional context for the issue

    Example:
        >>> issue = DiagnosticIssue(
        ...     category=DiagnosticCategory.COMMAND,
        ...     severity="critical",
        ...     check_name="command_exists",
        ...     message="Command 'mcp-ticketer' not found in PATH",
        ...     server_name="mcp-ticketer",
        ...     fix_suggestion="Install with: pipx install mcp-ticketer"
        ... )
    """

    category: DiagnosticCategory
    severity: Literal["critical", "warning", "info"]
    check_name: str
    message: str
    server_name: str | None
    fix_suggestion: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerDiagnostic:
    """Diagnostic results for a single MCP server.

    Attributes:
        name: Server name
        status: Server status (healthy, unreachable, error, unknown)
        response_time_ms: Response time in milliseconds (None if not tested)
        protocol_version: MCP protocol version from server (None if not tested)
        capabilities: Server capabilities (tools, resources, prompts)
        tool_count: Number of tools exposed
        resource_count: Number of resources exposed
        prompt_count: Number of prompts exposed
        error: Error message if status is error/unreachable

    Example:
        >>> diagnostic = ServerDiagnostic(
        ...     name="mcp-ticketer",
        ...     status=ServerStatus.HEALTHY,
        ...     response_time_ms=45.2,
        ...     protocol_version="2024-11-05",
        ...     capabilities={"tools": True, "resources": True, "prompts": False},
        ...     tool_count=5,
        ...     resource_count=2,
        ...     prompt_count=0
        ... )
    """

    name: str
    status: ServerStatus
    response_time_ms: float | None = None
    protocol_version: str | None = None
    capabilities: dict[str, bool] = field(default_factory=dict)
    tool_count: int = 0
    resource_count: int = 0
    prompt_count: int = 0
    error: str | None = None


@dataclass(frozen=True)
class DiagnosticReport:
    """Complete diagnostic report.

    Attributes:
        platform: Detected platform
        timestamp: When diagnostics were run
        checks_total: Total number of checks performed
        checks_passed: Number of checks that passed
        checks_failed: Number of checks that failed
        status: Overall health status
        issues: List of diagnostic issues found
        server_reports: Per-server diagnostic results
        recommendations: General recommendations for improvement

    Example:
        >>> report = DiagnosticReport(
        ...     platform=Platform.CLAUDE_CODE,
        ...     timestamp=datetime.now(),
        ...     checks_total=15,
        ...     checks_passed=12,
        ...     checks_failed=3,
        ...     status=DiagnosticStatus.DEGRADED,
        ...     issues=[...],
        ...     server_reports={"mcp-ticketer": ServerDiagnostic(...)},
        ...     recommendations=["Install missing command"]
        ... )
    """

    platform: Platform
    timestamp: datetime
    checks_total: int
    checks_passed: int
    checks_failed: int
    status: DiagnosticStatus
    issues: list[DiagnosticIssue] = field(default_factory=list)
    server_reports: dict[str, ServerDiagnostic] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def has_critical_issues(self) -> bool:
        """Check if report contains any critical issues.

        Returns:
            True if any critical-level issues found
        """
        return any(issue.severity == "critical" for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if report contains any warnings.

        Returns:
            True if any warning-level issues found
        """
        return any(issue.severity == "warning" for issue in self.issues)

    def summary(self) -> str:
        """Generate human-readable summary.

        Returns:
            Summary string with counts and status
        """
        critical = sum(1 for i in self.issues if i.severity == "critical")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        infos = sum(1 for i in self.issues if i.severity == "info")

        status_emoji = {
            DiagnosticStatus.HEALTHY: "\u2705",  # Green checkmark
            DiagnosticStatus.DEGRADED: "\u26a0\ufe0f",  # Warning sign
            DiagnosticStatus.CRITICAL: "\u274c",  # Red X
        }

        return (
            f"MCP Installation Diagnostics\n"
            f"{'=' * 30}\n"
            f"Platform: {self.platform.value}\n"
            f"Status: {status_emoji.get(self.status, '')} {self.status.value.upper()}\n"
            f"Checks: {self.checks_passed}/{self.checks_total} passed\n"
            f"  Critical: {critical}, Warnings: {warnings}, Info: {infos}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the report
        """
        return {
            "platform": self.platform.value,
            "timestamp": self.timestamp.isoformat(),
            "checks_total": self.checks_total,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "status": self.status.value,
            "issues": [
                {
                    "category": issue.category.value,
                    "severity": issue.severity,
                    "check_name": issue.check_name,
                    "message": issue.message,
                    "server_name": issue.server_name,
                    "fix_suggestion": issue.fix_suggestion,
                    "details": issue.details,
                }
                for issue in self.issues
            ],
            "server_reports": {
                name: {
                    "name": diag.name,
                    "status": diag.status.value,
                    "response_time_ms": diag.response_time_ms,
                    "protocol_version": diag.protocol_version,
                    "capabilities": diag.capabilities,
                    "tool_count": diag.tool_count,
                    "resource_count": diag.resource_count,
                    "prompt_count": diag.prompt_count,
                    "error": diag.error,
                }
                for name, diag in self.server_reports.items()
            },
            "recommendations": self.recommendations,
        }


# ============================================================================
# MCP Doctor
# ============================================================================


class MCPDoctor:
    """Comprehensive MCP installation diagnostics.

    Provides diagnostic capabilities for validating MCP server installations
    including configuration checks, command accessibility, environment variables,
    and JSON-RPC protocol compliance testing.

    Attributes:
        platform_info: Detected platform information
        timeout: Timeout for server tests in seconds
        verbose: Enable verbose logging

    Example:
        >>> from py_mcp_installer import PlatformDetector
        >>> detector = PlatformDetector()
        >>> info = detector.detect()
        >>> doctor = MCPDoctor(info)
        >>> report = doctor.diagnose(full=True)
        >>> print(report.summary())
    """

    # MCP protocol version for client identification
    PROTOCOL_VERSION = "2024-11-05"
    CLIENT_NAME = "mcp-doctor"
    CLIENT_VERSION = "1.0.0"

    def __init__(
        self,
        platform_info: PlatformInfo,
        timeout: float = 10.0,
        verbose: bool = False,
    ) -> None:
        """Initialize doctor with platform info.

        Args:
            platform_info: Platform information from PlatformDetector
            timeout: Timeout for server tests in seconds
            verbose: Enable verbose logging

        Example:
            >>> from py_mcp_installer import PlatformDetector
            >>> detector = PlatformDetector()
            >>> info = detector.detect()
            >>> doctor = MCPDoctor(info, timeout=15.0, verbose=True)
        """
        self.platform_info = platform_info
        self.timeout = timeout
        self.verbose = verbose
        self.config_path = platform_info.config_path or Path()

        # Determine config format based on platform
        if platform_info.platform == Platform.CODEX:
            self.config_format = ConfigFormat.TOML
        else:
            self.config_format = ConfigFormat.JSON

        self.config_manager = ConfigManager(self.config_path, self.config_format)

        if verbose:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

    def diagnose(self, full: bool = False) -> DiagnosticReport:
        """Run all diagnostics and return comprehensive report.

        Args:
            full: If True, also test server protocol compliance (slower)

        Returns:
            Complete diagnostic report with all issues and recommendations

        Example:
            >>> report = doctor.diagnose(full=False)  # Quick mode
            >>> if report.status == DiagnosticStatus.CRITICAL:
            ...     print("Critical issues found!")

            >>> report = doctor.diagnose(full=True)  # Full mode with server tests
            >>> for name, server in report.server_reports.items():
            ...     print(f"{name}: {server.status.value}")
        """
        logger.info(f"Running diagnostics (full={full})...")
        start_time = time.time()

        issues: list[DiagnosticIssue] = []
        recommendations: list[str] = []
        server_reports: dict[str, ServerDiagnostic] = {}
        checks_total = 0
        checks_passed = 0

        # Run platform checks
        platform_issues = self.check_platform()
        issues.extend(platform_issues)
        checks_total += 1
        if not any(i.severity == "critical" for i in platform_issues):
            checks_passed += 1

        # Run config checks
        config_issues = self.check_config()
        issues.extend(config_issues)
        checks_total += 1
        if not any(i.severity == "critical" for i in config_issues):
            checks_passed += 1

        # Get servers from config (if config is valid)
        servers = self._get_servers()

        # Run command checks for each server
        for server in servers:
            cmd_issues = self.check_command(server)
            issues.extend(cmd_issues)
            checks_total += 1
            if not any(i.severity == "critical" for i in cmd_issues):
                checks_passed += 1

        # Run environment checks for each server
        for server in servers:
            env_issues = self.check_environment(server)
            issues.extend(env_issues)
            checks_total += 1
            if not any(i.severity == "critical" for i in env_issues):
                checks_passed += 1

        # Run server protocol tests (full mode only)
        if full:
            for server in servers:
                server_diag = self.test_server(server)
                server_reports[server.name] = server_diag
                checks_total += 1

                if server_diag.status == ServerStatus.HEALTHY:
                    checks_passed += 1
                elif server_diag.status == ServerStatus.UNREACHABLE:
                    issues.append(
                        DiagnosticIssue(
                            category=DiagnosticCategory.SERVER,
                            severity="critical",
                            check_name="server_reachable",
                            message=f"Server '{server.name}' is unreachable",
                            server_name=server.name,
                            fix_suggestion=(
                                server_diag.error
                                or "Check that the server command is correct"
                            ),
                            details={"error": server_diag.error},
                        )
                    )
                elif server_diag.status == ServerStatus.ERROR:
                    issues.append(
                        DiagnosticIssue(
                            category=DiagnosticCategory.SERVER,
                            severity="warning",
                            check_name="server_protocol",
                            message=f"Server '{server.name}' returned error",
                            server_name=server.name,
                            fix_suggestion="Check server logs for details",
                            details={"error": server_diag.error},
                        )
                    )
        else:
            # Mark servers as unknown in quick mode
            for server in servers:
                server_reports[server.name] = ServerDiagnostic(
                    name=server.name,
                    status=ServerStatus.UNKNOWN,
                )

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, servers)

        # Calculate overall status
        status = self._calculate_status(issues)

        elapsed = time.time() - start_time
        logger.info(f"Diagnostics complete in {elapsed:.2f}s")

        return DiagnosticReport(
            platform=self.platform_info.platform,
            timestamp=datetime.now(),
            checks_total=checks_total,
            checks_passed=checks_passed,
            checks_failed=checks_total - checks_passed,
            status=status,
            issues=issues,
            server_reports=server_reports,
            recommendations=recommendations,
        )

    def check_platform(self) -> list[DiagnosticIssue]:
        """Check platform detection and configuration.

        Returns:
            List of platform-related diagnostic issues
        """
        issues: list[DiagnosticIssue] = []

        # Check platform is detected
        if self.platform_info.platform == Platform.UNKNOWN:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.PLATFORM,
                    severity="critical",
                    check_name="platform_detected",
                    message="No supported AI coding platform detected",
                    server_name=None,
                    fix_suggestion=(
                        "Install one of: Claude Code, Cursor, Windsurf, "
                        "Auggie, or Codex"
                    ),
                )
            )
            return issues

        # Check detection confidence
        if self.platform_info.confidence < 0.5:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.PLATFORM,
                    severity="warning",
                    check_name="platform_confidence",
                    message=(
                        f"Low confidence in platform detection "
                        f"({self.platform_info.confidence:.0%})"
                    ),
                    server_name=None,
                    fix_suggestion="Verify platform is installed correctly",
                    details={"confidence": self.platform_info.confidence},
                )
            )

        # Check config path exists
        if not self.platform_info.config_path:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.PLATFORM,
                    severity="warning",
                    check_name="config_path",
                    message="No configuration path detected for platform",
                    server_name=None,
                    fix_suggestion="Run the platform at least once to create config",
                )
            )

        logger.debug(f"Platform checks: {len(issues)} issues found")
        return issues

    def check_config(self) -> list[DiagnosticIssue]:
        """Check configuration file validity.

        Returns:
            List of config-related diagnostic issues
        """
        issues: list[DiagnosticIssue] = []

        # Check config file exists
        if not self.config_path.exists():
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.CONFIG,
                    severity="warning",
                    check_name="config_exists",
                    message=f"Configuration file not found: {self.config_path}",
                    server_name=None,
                    fix_suggestion=(
                        "Create config file or run installer to initialize"
                    ),
                )
            )
            return issues

        # Try to read and validate config
        try:
            config = self.config_manager.read()

            # Check for mcpServers key
            server_keys = ["mcpServers", "mcp_servers", "servers"]
            has_servers = any(key in config for key in server_keys)

            if not has_servers:
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.CONFIG,
                        severity="info",
                        check_name="config_has_servers",
                        message="No MCP servers configured",
                        server_name=None,
                        fix_suggestion="Add MCP servers using the installer",
                    )
                )

        except ConfigurationError as e:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.CONFIG,
                    severity="critical",
                    check_name="config_valid",
                    message=f"Configuration file is invalid: {e.message}",
                    server_name=None,
                    fix_suggestion=e.recovery_suggestion or "Fix or recreate config",
                )
            )

        logger.debug(f"Config checks: {len(issues)} issues found")
        return issues

    def check_command(self, server: MCPServerConfig) -> list[DiagnosticIssue]:
        """Check if server command is accessible.

        Args:
            server: Server configuration to check

        Returns:
            List of command-related diagnostic issues
        """
        issues: list[DiagnosticIssue] = []

        if not server.command:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.COMMAND,
                    severity="critical",
                    check_name="command_specified",
                    message=f"Server '{server.name}' has no command specified",
                    server_name=server.name,
                    fix_suggestion="Add command field to server configuration",
                )
            )
            return issues

        # Check if command exists in PATH
        resolved = resolve_command_path(server.command)
        if not resolved:
            fix_suggestion = self._suggest_command_install(server.command)
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.COMMAND,
                    severity="critical",
                    check_name="command_exists",
                    message=f"Command not found: {server.command}",
                    server_name=server.name,
                    fix_suggestion=fix_suggestion,
                )
            )

        logger.debug(f"Command checks for {server.name}: {len(issues)} issues found")
        return issues

    def check_environment(self, server: MCPServerConfig) -> list[DiagnosticIssue]:
        """Check environment variables for server.

        Args:
            server: Server configuration to check

        Returns:
            List of environment-related diagnostic issues
        """
        issues: list[DiagnosticIssue] = []

        for key, value in server.env.items():
            # Check for placeholder values
            if value.startswith("<") and value.endswith(">"):
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.ENVIRONMENT,
                        severity="warning",
                        check_name="env_placeholder",
                        message=(
                            f"Server '{server.name}' has placeholder env var: "
                            f"{key}={value}"
                        ),
                        server_name=server.name,
                        fix_suggestion=f"Set actual value for {key}",
                        details={"env_key": key, "env_value": value},
                    )
                )

            # Check for empty values
            if not value:
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.ENVIRONMENT,
                        severity="warning",
                        check_name="env_empty",
                        message=(f"Server '{server.name}' has empty env var: {key}"),
                        server_name=server.name,
                        fix_suggestion=f"Set a value for {key} or remove it",
                        details={"env_key": key},
                    )
                )

        logger.debug(
            f"Environment checks for {server.name}: {len(issues)} issues found"
        )
        return issues

    def test_server(self, server: MCPServerConfig) -> ServerDiagnostic:
        """Test single MCP server with full protocol validation.

        Starts the server process and tests JSON-RPC protocol compliance
        by performing the initialization handshake and querying capabilities.

        Args:
            server: Server configuration to test

        Returns:
            Complete server diagnostic results
        """
        logger.info(f"Testing server: {server.name}")

        # Check command exists first
        if not resolve_command_path(server.command):
            return ServerDiagnostic(
                name=server.name,
                status=ServerStatus.UNREACHABLE,
                error=f"Command not found: {server.command}",
            )

        # Build command line
        cmd = [server.command] + server.args

        # Prepare environment
        import os

        env = os.environ.copy()
        env.update(server.env)

        try:
            # Start server process
            start_time = time.time()
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            # Test initialization
            init_success, init_result = self._test_jsonrpc_initialize(proc)
            if not init_success:
                proc.terminate()
                return ServerDiagnostic(
                    name=server.name,
                    status=ServerStatus.ERROR,
                    error=init_result.get("error", "Initialization failed"),
                )

            # Send initialized notification
            self._send_jsonrpc_notification(proc, "initialized", {})

            # Get protocol version and capabilities from init response
            protocol_version = init_result.get("protocolVersion")
            capabilities = init_result.get("capabilities", {})

            # Test tools/list
            tools_success, tools = self._test_jsonrpc_tools_list(proc)
            tool_count = len(tools) if tools_success else 0

            # Test resources/list
            resources_success, resources = self._test_jsonrpc_resources_list(proc)
            resource_count = len(resources) if resources_success else 0

            # Test prompts/list
            prompts_success, prompts = self._test_jsonrpc_prompts_list(proc)
            prompt_count = len(prompts) if prompts_success else 0

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Clean up
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

            return ServerDiagnostic(
                name=server.name,
                status=ServerStatus.HEALTHY,
                response_time_ms=response_time_ms,
                protocol_version=protocol_version,
                capabilities={
                    "tools": "tools" in capabilities,
                    "resources": "resources" in capabilities,
                    "prompts": "prompts" in capabilities,
                },
                tool_count=tool_count,
                resource_count=resource_count,
                prompt_count=prompt_count,
            )

        except FileNotFoundError:
            return ServerDiagnostic(
                name=server.name,
                status=ServerStatus.UNREACHABLE,
                error=f"Command not found: {server.command}",
            )
        except subprocess.TimeoutExpired:
            return ServerDiagnostic(
                name=server.name,
                status=ServerStatus.UNREACHABLE,
                error=f"Server did not respond within {self.timeout}s",
            )
        except Exception as e:
            logger.error(f"Server test failed: {e}", exc_info=True)
            return ServerDiagnostic(
                name=server.name,
                status=ServerStatus.ERROR,
                error=str(e),
            )

    # ========================================================================
    # JSON-RPC Protocol Methods
    # ========================================================================

    def _send_jsonrpc(
        self, proc: subprocess.Popen[str], method: str, params: dict[str, Any], id: int
    ) -> dict[str, Any]:
        """Send JSON-RPC request and receive response.

        Args:
            proc: Server subprocess with stdin/stdout
            method: JSON-RPC method name
            params: Method parameters
            id: Request ID

        Returns:
            JSON-RPC response as dictionary

        Raises:
            TimeoutError: If response not received within timeout
            ValueError: If response is invalid JSON-RPC
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": id,
        }

        request_str = json.dumps(request) + "\n"
        logger.debug(f"Sending: {request_str.strip()}")

        assert proc.stdin is not None
        proc.stdin.write(request_str)
        proc.stdin.flush()

        # Read response with timeout
        response = self._read_jsonrpc_response(proc)
        logger.debug(f"Received: {response}")

        return response

    def _send_jsonrpc_notification(
        self, proc: subprocess.Popen[str], method: str, params: dict[str, Any]
    ) -> None:
        """Send JSON-RPC notification (no response expected).

        Args:
            proc: Server subprocess with stdin
            method: JSON-RPC method name
            params: Method parameters
        """
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        notification_str = json.dumps(notification) + "\n"
        logger.debug(f"Sending notification: {notification_str.strip()}")

        assert proc.stdin is not None
        proc.stdin.write(notification_str)
        proc.stdin.flush()

    def _read_jsonrpc_response(self, proc: subprocess.Popen[str]) -> dict[str, Any]:
        """Read JSON-RPC response with timeout.

        Args:
            proc: Server subprocess with stdout

        Returns:
            Parsed JSON-RPC response

        Raises:
            TimeoutError: If response not received within timeout
            ValueError: If response is invalid JSON
        """
        assert proc.stdout is not None

        # Use select for timeout on Unix systems
        import sys

        if sys.platform != "win32":
            readable, _, _ = select.select([proc.stdout], [], [], self.timeout)
            if not readable:
                raise TimeoutError(f"No response within {self.timeout}s")

        # Read line
        line = proc.stdout.readline()
        if not line:
            raise ValueError("Empty response from server")

        try:
            return json.loads(line)  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}") from e

    def _test_jsonrpc_initialize(
        self, proc: subprocess.Popen[str]
    ) -> tuple[bool, dict[str, Any]]:
        """Test JSON-RPC initialize handshake.

        Args:
            proc: Server subprocess

        Returns:
            Tuple of (success, result_or_error_dict)
        """
        try:
            response = self._send_jsonrpc(
                proc,
                "initialize",
                {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": self.CLIENT_NAME,
                        "version": self.CLIENT_VERSION,
                    },
                },
                id=1,
            )

            if "error" in response:
                return False, {
                    "error": response["error"].get("message", "Unknown error")
                }

            return True, response.get("result", {})

        except (TimeoutError, ValueError) as e:
            return False, {"error": str(e)}

    def _test_jsonrpc_tools_list(
        self, proc: subprocess.Popen[str]
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Test tools/list method.

        Args:
            proc: Server subprocess

        Returns:
            Tuple of (success, list_of_tools)
        """
        try:
            response = self._send_jsonrpc(proc, "tools/list", {}, id=2)

            if "error" in response:
                return False, []

            result = response.get("result", {})
            return True, result.get("tools", [])

        except (TimeoutError, ValueError):
            return False, []

    def _test_jsonrpc_resources_list(
        self, proc: subprocess.Popen[str]
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Test resources/list method.

        Args:
            proc: Server subprocess

        Returns:
            Tuple of (success, list_of_resources)
        """
        try:
            response = self._send_jsonrpc(proc, "resources/list", {}, id=3)

            if "error" in response:
                return False, []

            result = response.get("result", {})
            return True, result.get("resources", [])

        except (TimeoutError, ValueError):
            return False, []

    def _test_jsonrpc_prompts_list(
        self, proc: subprocess.Popen[str]
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Test prompts/list method.

        Args:
            proc: Server subprocess

        Returns:
            Tuple of (success, list_of_prompts)
        """
        try:
            response = self._send_jsonrpc(proc, "prompts/list", {}, id=4)

            if "error" in response:
                return False, []

            result = response.get("result", {})
            return True, result.get("prompts", [])

        except (TimeoutError, ValueError):
            return False, []

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _get_servers(self) -> list[MCPServerConfig]:
        """Get servers from configuration.

        Returns:
            List of server configurations (empty if config invalid)
        """
        try:
            config = self.config_manager.read()
        except ConfigurationError:
            return []

        servers: list[MCPServerConfig] = []
        server_keys = ["mcpServers", "mcp_servers", "servers"]

        for key in server_keys:
            if key in config and isinstance(config[key], dict):
                for name, server_data in config[key].items():
                    if isinstance(server_data, dict):
                        servers.append(
                            MCPServerConfig(
                                name=name,
                                command=server_data.get("command", ""),
                                args=server_data.get("args", []),
                                env=server_data.get("env", {}),
                                description=server_data.get("description", ""),
                            )
                        )
                break

        return servers

    def _suggest_command_install(self, command: str) -> str:
        """Suggest how to install missing command.

        Args:
            command: Command that is missing

        Returns:
            Installation suggestion
        """
        suggestions = {
            "uv": "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh",
            "python": "Install Python: https://python.org/downloads",
            "node": "Install Node.js: https://nodejs.org",
            "npm": "Install Node.js (includes npm): https://nodejs.org",
            "npx": "Install Node.js (includes npx): https://nodejs.org",
        }

        return suggestions.get(
            command, f"Install {command} and ensure it's in your PATH"
        )

    def _generate_recommendations(
        self, issues: list[DiagnosticIssue], servers: list[MCPServerConfig]
    ) -> list[str]:
        """Generate recommendations based on issues found.

        Args:
            issues: List of diagnostic issues
            servers: List of server configurations

        Returns:
            List of recommendation strings
        """
        recommendations: list[str] = []

        # Count issues by category
        critical_count = sum(1 for i in issues if i.severity == "critical")

        # Add recommendations based on issues
        if critical_count > 0:
            recommendations.append(
                f"Address {critical_count} critical issue(s) before using MCP servers"
            )

        # Check for missing commands
        missing_commands = [i for i in issues if i.check_name == "command_exists"]
        if missing_commands:
            recommendations.append(
                f"Install {len(missing_commands)} missing command(s)"
            )

        # Check for env placeholders
        placeholder_issues = [i for i in issues if i.check_name == "env_placeholder"]
        if placeholder_issues:
            recommendations.append(
                f"Configure {len(placeholder_issues)} environment variable(s)"
            )

        # Check if using uv
        non_uv_servers = [s for s in servers if s.command != "uv"]
        if non_uv_servers and len(non_uv_servers) < len(servers):
            # Only recommend if some servers already use uv
            recommendations.append(
                f"Consider migrating {len(non_uv_servers)} server(s) to 'uv run' for faster startup"
            )

        return recommendations

    def _calculate_status(self, issues: list[DiagnosticIssue]) -> DiagnosticStatus:
        """Calculate overall diagnostic status.

        Args:
            issues: List of diagnostic issues

        Returns:
            Overall status (healthy, degraded, critical)
        """
        if any(i.severity == "critical" for i in issues):
            return DiagnosticStatus.CRITICAL

        if any(i.severity == "warning" for i in issues):
            return DiagnosticStatus.DEGRADED

        return DiagnosticStatus.HEALTHY
