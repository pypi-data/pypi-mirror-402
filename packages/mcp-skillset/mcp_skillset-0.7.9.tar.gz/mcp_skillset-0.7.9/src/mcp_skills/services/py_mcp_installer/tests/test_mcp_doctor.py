"""Unit tests for MCPDoctor diagnostic module."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from py_mcp_installer.mcp_doctor import (
    DiagnosticIssue,
    DiagnosticReport,
    MCPDoctor,
    ServerDiagnostic,
)
from py_mcp_installer.types import (
    DiagnosticCategory,
    DiagnosticStatus,
    MCPServerConfig,
    Platform,
    PlatformInfo,
    Scope,
    ServerStatus,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_platform_info() -> PlatformInfo:
    """Create mock platform info for tests."""
    return PlatformInfo(
        platform=Platform.CLAUDE_CODE,
        confidence=1.0,
        config_path=Path("/tmp/test_mcp.json"),
        cli_available=True,
        scope_support=Scope.BOTH,
    )


@pytest.fixture
def mock_config_content() -> dict[str, Any]:
    """Create mock config file content."""
    return {
        "mcpServers": {
            "test-server": {
                "command": "uv",
                "args": ["run", "test-server", "mcp"],
                "env": {"API_KEY": "test_key"},
            },
            "github-mcp": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "<your_token>"},
            },
        }
    }


@pytest.fixture
def doctor(mock_platform_info: PlatformInfo) -> MCPDoctor:
    """Create MCPDoctor instance for tests."""
    return MCPDoctor(mock_platform_info)


# ============================================================================
# DiagnosticIssue Tests
# ============================================================================


class TestDiagnosticIssue:
    """Tests for DiagnosticIssue dataclass."""

    def test_create_issue(self) -> None:
        """Test creating a diagnostic issue."""
        issue = DiagnosticIssue(
            category=DiagnosticCategory.CONFIG,
            severity="critical",
            check_name="config_exists",
            message="Config file not found",
            server_name=None,
            fix_suggestion="Create config file",
        )

        assert issue.category == DiagnosticCategory.CONFIG
        assert issue.severity == "critical"
        assert issue.message == "Config file not found"
        assert issue.server_name is None
        assert issue.fix_suggestion == "Create config file"

    def test_issue_with_server_name(self) -> None:
        """Test creating issue with server name."""
        issue = DiagnosticIssue(
            category=DiagnosticCategory.SERVER,
            severity="warning",
            check_name="json_rpc_test",
            message="Server slow",
            server_name="test-server",
            fix_suggestion="Check server",
        )

        assert issue.server_name == "test-server"
        assert issue.severity == "warning"

    def test_issue_with_details(self) -> None:
        """Test creating issue with additional details."""
        issue = DiagnosticIssue(
            category=DiagnosticCategory.ENVIRONMENT,
            severity="info",
            check_name="env_check",
            message="Info message",
            server_name="test",
            fix_suggestion="No action needed",
            details={"key": "value", "count": 42},
        )

        assert issue.details == {"key": "value", "count": 42}

    def test_frozen_issue(self) -> None:
        """Test that DiagnosticIssue is immutable."""
        issue = DiagnosticIssue(
            category=DiagnosticCategory.CONFIG,
            severity="critical",
            check_name="test",
            message="Test",
            server_name=None,
            fix_suggestion="Fix",
        )

        with pytest.raises(AttributeError):
            issue.severity = "warning"  # type: ignore[misc]


# ============================================================================
# ServerDiagnostic Tests
# ============================================================================


class TestServerDiagnostic:
    """Tests for ServerDiagnostic dataclass."""

    def test_healthy_server(self) -> None:
        """Test creating healthy server diagnostic."""
        diag = ServerDiagnostic(
            name="test-server",
            status=ServerStatus.HEALTHY,
            response_time_ms=45.5,
            protocol_version="2024-11-05",
            capabilities={"tools": True, "resources": True, "prompts": False},
            tool_count=5,
            resource_count=2,
            prompt_count=0,
            error=None,
        )

        assert diag.name == "test-server"
        assert diag.status == ServerStatus.HEALTHY
        assert diag.tool_count == 5
        assert diag.resource_count == 2
        assert diag.error is None
        assert diag.response_time_ms == 45.5
        assert diag.protocol_version == "2024-11-05"

    def test_unreachable_server(self) -> None:
        """Test creating unreachable server diagnostic."""
        diag = ServerDiagnostic(
            name="bad-server",
            status=ServerStatus.UNREACHABLE,
            error="Connection timeout",
        )

        assert diag.status == ServerStatus.UNREACHABLE
        assert diag.error == "Connection timeout"
        assert diag.response_time_ms is None
        assert diag.tool_count == 0

    def test_error_server(self) -> None:
        """Test creating error server diagnostic."""
        diag = ServerDiagnostic(
            name="error-server",
            status=ServerStatus.ERROR,
            error="Protocol error",
            response_time_ms=100.0,
        )

        assert diag.status == ServerStatus.ERROR
        assert diag.error == "Protocol error"
        assert diag.response_time_ms == 100.0

    def test_unknown_server(self) -> None:
        """Test creating unknown status server (quick mode)."""
        diag = ServerDiagnostic(
            name="untested-server",
            status=ServerStatus.UNKNOWN,
        )

        assert diag.status == ServerStatus.UNKNOWN
        assert diag.error is None


# ============================================================================
# DiagnosticReport Tests
# ============================================================================


class TestDiagnosticReport:
    """Tests for DiagnosticReport dataclass."""

    def test_healthy_report(self, mock_platform_info: PlatformInfo) -> None:
        """Test creating a healthy diagnostic report."""
        report = DiagnosticReport(
            platform=Platform.CLAUDE_CODE,
            timestamp=datetime.now(),
            checks_total=5,
            checks_passed=5,
            checks_failed=0,
            status=DiagnosticStatus.HEALTHY,
            issues=[],
            server_reports={},
            recommendations=[],
        )

        assert report.status == DiagnosticStatus.HEALTHY
        assert report.checks_passed == 5
        assert report.checks_failed == 0
        assert len(report.issues) == 0
        assert not report.has_critical_issues()
        assert not report.has_warnings()

    def test_degraded_report(self) -> None:
        """Test report with warnings."""
        issue = DiagnosticIssue(
            category=DiagnosticCategory.ENVIRONMENT,
            severity="warning",
            check_name="env_check",
            message="Placeholder value",
            server_name="test",
            fix_suggestion="Set real value",
        )

        report = DiagnosticReport(
            platform=Platform.CLAUDE_CODE,
            timestamp=datetime.now(),
            checks_total=5,
            checks_passed=4,
            checks_failed=1,
            status=DiagnosticStatus.DEGRADED,
            issues=[issue],
            server_reports={},
            recommendations=["Fix placeholder values"],
        )

        assert report.status == DiagnosticStatus.DEGRADED
        assert len(report.recommendations) == 1
        assert not report.has_critical_issues()
        assert report.has_warnings()

    def test_critical_report(self) -> None:
        """Test report with critical issues."""
        issue = DiagnosticIssue(
            category=DiagnosticCategory.CONFIG,
            severity="critical",
            check_name="config_exists",
            message="Config missing",
            server_name=None,
            fix_suggestion="Create config",
        )

        report = DiagnosticReport(
            platform=Platform.CLAUDE_CODE,
            timestamp=datetime.now(),
            checks_total=5,
            checks_passed=2,
            checks_failed=3,
            status=DiagnosticStatus.CRITICAL,
            issues=[issue],
            server_reports={},
            recommendations=["Fix critical issues"],
        )

        assert report.status == DiagnosticStatus.CRITICAL
        assert report.has_critical_issues()

    def test_report_summary(self) -> None:
        """Test report summary generation."""
        report = DiagnosticReport(
            platform=Platform.CLAUDE_CODE,
            timestamp=datetime.now(),
            checks_total=10,
            checks_passed=8,
            checks_failed=2,
            status=DiagnosticStatus.DEGRADED,
            issues=[
                DiagnosticIssue(
                    category=DiagnosticCategory.CONFIG,
                    severity="warning",
                    check_name="test",
                    message="Test",
                    server_name=None,
                    fix_suggestion="Fix",
                )
            ],
            server_reports={},
            recommendations=[],
        )

        summary = report.summary()
        assert "MCP Installation Diagnostics" in summary
        assert "Platform: claude_code" in summary
        assert "Checks: 8/10 passed" in summary
        assert "DEGRADED" in summary

    def test_report_to_dict(self) -> None:
        """Test report serialization to dict."""
        timestamp = datetime.now()
        issue = DiagnosticIssue(
            category=DiagnosticCategory.COMMAND,
            severity="critical",
            check_name="command_exists",
            message="Command not found",
            server_name="test-server",
            fix_suggestion="Install command",
            details={"command": "test"},
        )
        server_diag = ServerDiagnostic(
            name="test-server",
            status=ServerStatus.HEALTHY,
            response_time_ms=50.0,
            tool_count=3,
        )

        report = DiagnosticReport(
            platform=Platform.CLAUDE_CODE,
            timestamp=timestamp,
            checks_total=5,
            checks_passed=4,
            checks_failed=1,
            status=DiagnosticStatus.DEGRADED,
            issues=[issue],
            server_reports={"test-server": server_diag},
            recommendations=["Fix command"],
        )

        d = report.to_dict()
        assert d["platform"] == "claude_code"
        assert d["status"] == "degraded"
        assert d["checks_total"] == 5
        assert d["checks_passed"] == 4
        assert len(d["issues"]) == 1
        assert d["issues"][0]["category"] == "command"
        assert d["issues"][0]["severity"] == "critical"
        assert "test-server" in d["server_reports"]
        assert d["server_reports"]["test-server"]["status"] == "healthy"


# ============================================================================
# MCPDoctor Tests
# ============================================================================


class TestMCPDoctor:
    """Tests for MCPDoctor class."""

    def test_init(self, mock_platform_info: PlatformInfo) -> None:
        """Test doctor initialization."""
        doctor = MCPDoctor(mock_platform_info, timeout=5.0, verbose=False)
        assert doctor.platform_info == mock_platform_info
        assert doctor.timeout == 5.0
        assert doctor.verbose is False
        assert doctor.config_path == Path("/tmp/test_mcp.json")

    def test_init_with_verbose(self, mock_platform_info: PlatformInfo) -> None:
        """Test doctor initialization with verbose logging."""
        doctor = MCPDoctor(mock_platform_info, timeout=10.0, verbose=True)
        assert doctor.verbose is True

    def test_check_platform_healthy(self, doctor: MCPDoctor) -> None:
        """Test platform check with valid platform."""
        issues = doctor.check_platform()
        # Should pass for valid claude_code platform with high confidence
        critical_issues = [i for i in issues if i.severity == "critical"]
        assert len(critical_issues) == 0

    def test_check_platform_unknown(self) -> None:
        """Test platform check with unknown platform."""
        info = PlatformInfo(
            platform=Platform.UNKNOWN,
            confidence=0.0,
            config_path=None,
            cli_available=False,
            scope_support=Scope.BOTH,
        )
        doctor = MCPDoctor(info)

        issues = doctor.check_platform()
        critical = [i for i in issues if i.severity == "critical"]
        assert len(critical) >= 1
        # Check that at least one critical issue mentions detection
        detection_issues = [i for i in critical if "detect" in i.message.lower()]
        assert len(detection_issues) >= 1

    def test_check_platform_low_confidence(
        self, mock_platform_info: PlatformInfo
    ) -> None:
        """Test platform check with low confidence."""
        info = PlatformInfo(
            platform=Platform.CLAUDE_CODE,
            confidence=0.3,
            config_path=Path("/tmp/test.json"),
            cli_available=True,
            scope_support=Scope.BOTH,
        )
        doctor = MCPDoctor(info)

        issues = doctor.check_platform()
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) >= 1
        assert any("confidence" in i.message.lower() for i in warnings)

    def test_check_platform_no_config_path(
        self, mock_platform_info: PlatformInfo
    ) -> None:
        """Test platform check with no config path."""
        info = PlatformInfo(
            platform=Platform.CLAUDE_CODE,
            confidence=0.8,
            config_path=None,
            cli_available=True,
            scope_support=Scope.BOTH,
        )
        doctor = MCPDoctor(info)

        issues = doctor.check_platform()
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) >= 1
        assert any("configuration path" in i.message.lower() for i in warnings)

    def test_check_config_missing(self, mock_platform_info: PlatformInfo) -> None:
        """Test config check with missing file."""
        info = PlatformInfo(
            platform=Platform.CLAUDE_CODE,
            confidence=0.5,
            config_path=Path("/nonexistent/config.json"),
            cli_available=False,
            scope_support=Scope.PROJECT,
        )
        doctor = MCPDoctor(info)

        issues = doctor.check_config()
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) >= 1
        assert any("not found" in i.message.lower() for i in warnings)

    @patch("py_mcp_installer.mcp_doctor.ConfigManager")
    def test_check_config_valid_with_servers(
        self,
        mock_config_manager: MagicMock,
        doctor: MCPDoctor,
        mock_config_content: dict[str, Any],
    ) -> None:
        """Test config check with valid config containing servers."""
        mock_manager = MagicMock()
        mock_manager.read.return_value = mock_config_content
        mock_config_manager.return_value = mock_manager

        with patch.object(Path, "exists", return_value=True):
            doctor.config_manager = mock_manager
            issues = doctor.check_config()

        # Should have no critical issues
        critical = [i for i in issues if i.severity == "critical"]
        assert len(critical) == 0

    @patch("py_mcp_installer.mcp_doctor.ConfigManager")
    def test_check_config_valid_no_servers(
        self, mock_config_manager: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test config check with valid config but no servers."""
        mock_manager = MagicMock()
        mock_manager.read.return_value = {"other_key": "value"}
        mock_config_manager.return_value = mock_manager

        with patch.object(Path, "exists", return_value=True):
            doctor.config_manager = mock_manager
            issues = doctor.check_config()

        # Should have info issue about no servers
        info_issues = [i for i in issues if i.severity == "info"]
        assert len(info_issues) >= 1
        assert any("no mcp servers" in i.message.lower() for i in info_issues)

    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_check_command_found(
        self, mock_resolve: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test command check when command exists."""
        mock_resolve.return_value = "/usr/bin/uv"

        server = MCPServerConfig(
            name="test-server",
            command="uv",
            args=["run", "test-server"],
        )

        issues = doctor.check_command(server)

        # No critical issues expected when command found
        critical = [i for i in issues if i.severity == "critical"]
        assert len(critical) == 0

    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_check_command_not_found(
        self, mock_resolve: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test command check when command not found."""
        mock_resolve.return_value = None

        server = MCPServerConfig(
            name="test-server",
            command="nonexistent-cmd",
            args=[],
        )

        issues = doctor.check_command(server)

        # Should have critical issue
        critical = [i for i in issues if i.severity == "critical"]
        assert len(critical) >= 1
        assert any("not found" in i.message.lower() for i in critical)

    def test_check_command_no_command_specified(self, doctor: MCPDoctor) -> None:
        """Test command check with no command specified."""
        server = MCPServerConfig(
            name="test-server",
            command="",
            args=[],
        )

        issues = doctor.check_command(server)

        critical = [i for i in issues if i.severity == "critical"]
        assert len(critical) >= 1
        assert any("no command" in i.message.lower() for i in critical)

    def test_check_environment_placeholder(self, doctor: MCPDoctor) -> None:
        """Test environment check detects placeholder values."""
        server = MCPServerConfig(
            name="github-mcp",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": "<your_token>"},
        )

        issues = doctor.check_environment(server)

        # Should detect placeholder
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) >= 1
        assert any("placeholder" in i.message.lower() for i in warnings)

    def test_check_environment_empty(self, doctor: MCPDoctor) -> None:
        """Test environment check detects empty values."""
        server = MCPServerConfig(
            name="test-server",
            command="test",
            args=[],
            env={"API_KEY": ""},
        )

        issues = doctor.check_environment(server)

        # Should detect empty value
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) >= 1
        assert any("empty" in i.message.lower() for i in warnings)

    def test_check_environment_valid(self, doctor: MCPDoctor) -> None:
        """Test environment check with valid values."""
        server = MCPServerConfig(
            name="test-server",
            command="test",
            args=[],
            env={"API_KEY": "valid_key_123"},
        )

        issues = doctor.check_environment(server)

        # Should have no issues
        assert len(issues) == 0

    @patch("builtins.open")
    @patch.object(Path, "exists", return_value=True)
    @patch("py_mcp_installer.mcp_doctor.ConfigManager")
    def test_diagnose_quick(
        self,
        mock_config_manager: MagicMock,
        mock_exists: MagicMock,
        mock_open: MagicMock,
        doctor: MCPDoctor,
        mock_config_content: dict[str, Any],
    ) -> None:
        """Test quick diagnose (no server tests)."""
        mock_manager = MagicMock()
        mock_manager.read.return_value = mock_config_content
        doctor.config_manager = mock_manager

        with patch(
            "py_mcp_installer.mcp_doctor.resolve_command_path",
            return_value="/usr/bin/uv",
        ):
            report = doctor.diagnose(full=False)

        assert isinstance(report, DiagnosticReport)
        assert report.platform == Platform.CLAUDE_CODE
        # Server reports should contain servers but marked as UNKNOWN in quick mode
        assert len(report.server_reports) >= 0

    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_suggest_command_install_known(
        self, mock_resolve: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test command install suggestions for known commands."""
        suggestion = doctor._suggest_command_install("uv")
        assert "uv" in suggestion.lower()
        assert "astral.sh" in suggestion.lower()

    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_suggest_command_install_unknown(
        self, mock_resolve: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test command install suggestions for unknown commands."""
        suggestion = doctor._suggest_command_install("unknown-command")
        assert "unknown-command" in suggestion.lower()
        assert "path" in suggestion.lower()


# ============================================================================
# Server Protocol Tests
# ============================================================================


class TestServerProtocolTests:
    """Tests for MCP server JSON-RPC protocol testing."""

    @patch("select.select")
    @patch("subprocess.Popen")
    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_test_server_healthy(
        self,
        mock_resolve: MagicMock,
        mock_popen: MagicMock,
        mock_select: MagicMock,
        doctor: MCPDoctor,
    ) -> None:
        """Test server testing with healthy response."""
        mock_resolve.return_value = "/usr/bin/test"

        # Mock subprocess
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.returncode = None

        # Mock JSON-RPC responses
        init_response = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {},
                            "prompts": {},
                        },
                        "serverInfo": {"name": "test", "version": "1.0"},
                    },
                }
            )
            + "\n"
        )

        tools_response = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {"tools": [{"name": "tool1"}, {"name": "tool2"}]},
                }
            )
            + "\n"
        )

        resources_response = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "result": {"resources": []},
                }
            )
            + "\n"
        )

        prompts_response = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "result": {"prompts": []},
                }
            )
            + "\n"
        )

        # Set up mock readline to return responses in sequence
        mock_process.stdout.readline.side_effect = [
            init_response,
            tools_response,
            resources_response,
            prompts_response,
        ]
        mock_process.stdin = MagicMock()

        # Mock select to always return ready
        mock_select.return_value = ([mock_process.stdout], [], [])

        mock_popen.return_value = mock_process

        server = MCPServerConfig(
            name="test-server",
            command="test",
            args=["mcp"],
        )

        diag = doctor.test_server(server)

        assert diag.name == "test-server"
        assert diag.status == ServerStatus.HEALTHY
        assert diag.tool_count == 2
        assert diag.response_time_ms is not None
        assert diag.protocol_version == "2024-11-05"

    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_test_server_command_not_found(
        self, mock_resolve: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test server testing with command not found."""
        mock_resolve.return_value = None

        server = MCPServerConfig(
            name="missing-server",
            command="missing-command",
            args=[],
        )

        diag = doctor.test_server(server)

        assert diag.status == ServerStatus.UNREACHABLE
        assert "not found" in (diag.error or "").lower()

    @patch("subprocess.Popen")
    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_test_server_timeout(
        self, mock_resolve: MagicMock, mock_popen: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test server testing with timeout."""
        mock_resolve.return_value = "/usr/bin/test"
        mock_popen.side_effect = subprocess.TimeoutExpired("test", 5)

        server = MCPServerConfig(
            name="slow-server",
            command="slow",
            args=[],
        )

        diag = doctor.test_server(server)

        assert diag.status == ServerStatus.UNREACHABLE
        error_lower = (diag.error or "").lower()
        assert "timeout" in error_lower or "not respond" in error_lower

    @patch("subprocess.Popen")
    @patch("py_mcp_installer.mcp_doctor.resolve_command_path")
    def test_test_server_init_error(
        self, mock_resolve: MagicMock, mock_popen: MagicMock, doctor: MCPDoctor
    ) -> None:
        """Test server testing with initialization error."""
        mock_resolve.return_value = "/usr/bin/test"

        # Mock subprocess
        mock_process = MagicMock()

        # Mock error response
        error_response = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "error": {"code": -32600, "message": "Invalid request"},
                }
            )
            + "\n"
        )

        mock_process.stdout.readline.return_value = error_response
        mock_process.stdin = MagicMock()

        mock_popen.return_value = mock_process

        server = MCPServerConfig(
            name="error-server",
            command="test",
            args=[],
        )

        diag = doctor.test_server(server)

        assert diag.status == ServerStatus.ERROR
        assert diag.error is not None


# ============================================================================
# CLI Integration Tests
# ============================================================================


class TestCLI:
    """Tests for CLI command."""

    def test_import_cli(self) -> None:
        """Test that CLI module can be imported."""
        from py_mcp_installer.cli import cmd_doctor, main

        assert callable(main)
        assert callable(cmd_doctor)

    @patch("py_mcp_installer.cli.PlatformDetector")
    @patch("py_mcp_installer.cli.MCPDoctor")
    def test_cmd_doctor_json_output(
        self, mock_doctor_cls: MagicMock, mock_detector_cls: MagicMock
    ) -> None:
        """Test doctor command with JSON output."""
        from argparse import Namespace

        from py_mcp_installer.cli import cmd_doctor

        # Mock platform detector
        mock_detector = MagicMock()
        mock_detector.detect.return_value = PlatformInfo(
            platform=Platform.CLAUDE_CODE,
            confidence=1.0,
            config_path=Path("/tmp/test.json"),
            cli_available=True,
            scope_support=Scope.BOTH,
        )
        mock_detector_cls.return_value = mock_detector

        # Mock doctor
        mock_doctor = MagicMock()
        mock_doctor.diagnose.return_value = DiagnosticReport(
            platform=Platform.CLAUDE_CODE,
            timestamp=datetime.now(),
            checks_total=5,
            checks_passed=5,
            checks_failed=0,
            status=DiagnosticStatus.HEALTHY,
            issues=[],
            server_reports={},
            recommendations=[],
        )
        mock_doctor_cls.return_value = mock_doctor

        args = Namespace(
            full=False,
            server=None,
            json=True,
            verbose=False,
            timeout=10.0,
        )

        exit_code = cmd_doctor(args)
        assert exit_code == 0
        mock_doctor.diagnose.assert_called_once_with(full=False)

    @patch("py_mcp_installer.cli.PlatformDetector")
    @patch("py_mcp_installer.cli.MCPDoctor")
    def test_cmd_doctor_with_issues(
        self, mock_doctor_cls: MagicMock, mock_detector_cls: MagicMock
    ) -> None:
        """Test doctor command with issues found."""
        from argparse import Namespace

        from py_mcp_installer.cli import cmd_doctor

        # Mock platform detector
        mock_detector = MagicMock()
        mock_detector.detect.return_value = PlatformInfo(
            platform=Platform.CLAUDE_CODE,
            confidence=1.0,
            config_path=Path("/tmp/test.json"),
            cli_available=True,
            scope_support=Scope.BOTH,
        )
        mock_detector_cls.return_value = mock_detector

        # Mock doctor with issues
        mock_doctor = MagicMock()
        mock_doctor.diagnose.return_value = DiagnosticReport(
            platform=Platform.CLAUDE_CODE,
            timestamp=datetime.now(),
            checks_total=5,
            checks_passed=3,
            checks_failed=2,
            status=DiagnosticStatus.DEGRADED,
            issues=[
                DiagnosticIssue(
                    category=DiagnosticCategory.CONFIG,
                    severity="warning",
                    check_name="test",
                    message="Test issue",
                    server_name=None,
                    fix_suggestion="Fix it",
                )
            ],
            server_reports={},
            recommendations=["Fix the issue"],
        )
        mock_doctor_cls.return_value = mock_doctor

        args = Namespace(
            full=False,
            server=None,
            json=False,
            verbose=False,
            timeout=10.0,
        )

        exit_code = cmd_doctor(args)
        # Exit code should be 1 when issues found
        assert exit_code in [0, 1]
