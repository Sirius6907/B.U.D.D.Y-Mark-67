"""
tools/kali_adapter.py — Kali Linux WSL Tool Adapter
=====================================================
Governed execution bridge between B.U.D.D.Y's OPEV runtime and 25+ Kali
tools running inside the user's WSL Kali Linux environment.

Architecture:
  1. TOOL_REGISTRY maps tool names → metadata (tier, scopes, timeout, parser)
  2. TargetScopeValidator enforces allowlisted targets from kali_targets.json
  3. KaliAdapter.execute() is the single entry-point for the executor
  4. All output capped at 1 MB, all executions journaled

Safety:
  - Every Kali scope is DANGEROUS → always requires approval
  - Tier 3 tools (hydra, sqlmap --dump, msfconsole) require explicit user confirmation
  - Target allowlist prevents unauthorized network scanning
  - localhost / 127.0.0.1 pre-authorized by default
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from agent.models import ActionResult, PermissionScope

__all__ = ["KaliAdapter", "TargetScopeValidator", "KaliToolMeta", "KALI_TOOL_REGISTRY"]


# ─── Constants ────────────────────────────────────────────────────────────────

WSL_DISTRO = "kali-linux"
MAX_OUTPUT_BYTES = 1_048_576  # 1 MB cap
DEFAULT_TIMEOUT = 300         # 5 min default
CONFIG_DIR = Path.home() / ".buddy"
TARGETS_FILE = CONFIG_DIR / "kali_targets.json"

# Pre-authorized targets (always allowed without explicit allowlisting)
_PRE_AUTHORIZED = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",  # for listeners only, not scanning targets
})


# ─── Tool Tier Classification ────────────────────────────────────────────────

class KaliTier(str, Enum):
    """Risk tier for Kali tools."""
    TIER_1 = "tier_1"  # Passive recon: nmap discovery, whois, searchsploit
    TIER_2 = "tier_2"  # Active scanning: nikto, gobuster, nuclei, wpscan
    TIER_3 = "tier_3"  # Exploitation/intrusive: hydra, sqlmap --dump, msfconsole


@dataclass(slots=True)
class KaliToolMeta:
    """Metadata for a single Kali tool."""
    name: str
    binary: str
    tier: KaliTier
    scopes: frozenset[PermissionScope]
    default_timeout: int = DEFAULT_TIMEOUT
    description: str = ""
    output_parser: str = "raw"  # raw | json | grep


# ─── Tool Registry ───────────────────────────────────────────────────────────

KALI_TOOL_REGISTRY: dict[str, KaliToolMeta] = {
    # ── TIER 1: Passive Recon ─────────────────────────────────────────────
    "nmap_discovery": KaliToolMeta(
        name="nmap_discovery", binary="nmap",
        tier=KaliTier.TIER_1,
        scopes=frozenset({PermissionScope.CAN_RECON}),
        default_timeout=120,
        description="Network host discovery and port scanning",
    ),
    "whois": KaliToolMeta(
        name="whois", binary="whois",
        tier=KaliTier.TIER_1,
        scopes=frozenset({PermissionScope.CAN_RECON}),
        default_timeout=30,
        description="Domain registration lookup",
    ),
    "searchsploit": KaliToolMeta(
        name="searchsploit", binary="searchsploit",
        tier=KaliTier.TIER_1,
        scopes=frozenset({PermissionScope.CAN_RECON}),
        default_timeout=30,
        description="Exploit database search (offline)",
    ),
    "subfinder": KaliToolMeta(
        name="subfinder", binary="subfinder",
        tier=KaliTier.TIER_1,
        scopes=frozenset({PermissionScope.CAN_RECON}),
        default_timeout=120,
        description="Subdomain enumeration",
    ),
    "amass_enum": KaliToolMeta(
        name="amass_enum", binary="amass",
        tier=KaliTier.TIER_1,
        scopes=frozenset({PermissionScope.CAN_RECON}),
        default_timeout=300,
        description="Attack surface mapping and subdomain enumeration",
    ),
    "whatweb": KaliToolMeta(
        name="whatweb", binary="whatweb",
        tier=KaliTier.TIER_1,
        scopes=frozenset({PermissionScope.CAN_RECON}),
        default_timeout=60,
        description="Web technology fingerprinting",
    ),
    "dnsrecon": KaliToolMeta(
        name="dnsrecon", binary="dnsrecon",
        tier=KaliTier.TIER_1,
        scopes=frozenset({PermissionScope.CAN_RECON}),
        default_timeout=120,
        description="DNS enumeration and zone transfer testing",
    ),

    # ── TIER 2: Active Scanning ───────────────────────────────────────────
    "nikto": KaliToolMeta(
        name="nikto", binary="nikto",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=600,
        description="Web server vulnerability scanner",
    ),
    "gobuster": KaliToolMeta(
        name="gobuster", binary="gobuster",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=300,
        description="Directory and DNS brute-forcing",
    ),
    "ffuf": KaliToolMeta(
        name="ffuf", binary="ffuf",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=300,
        description="Web fuzzer for directories, parameters, and vhosts",
    ),
    "nuclei": KaliToolMeta(
        name="nuclei", binary="nuclei",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=600,
        description="Template-based vulnerability scanner",
    ),
    "wpscan": KaliToolMeta(
        name="wpscan", binary="wpscan",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=300,
        description="WordPress vulnerability scanner",
    ),
    "nmap_vuln": KaliToolMeta(
        name="nmap_vuln", binary="nmap",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=600,
        description="Nmap with vulnerability scripts (--script vuln)",
    ),
    "masscan": KaliToolMeta(
        name="masscan", binary="masscan",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=300,
        description="High-speed port scanner",
    ),
    "dirb": KaliToolMeta(
        name="dirb", binary="dirb",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=300,
        description="Web content directory scanner",
    ),
    "enum4linux": KaliToolMeta(
        name="enum4linux", binary="enum4linux",
        tier=KaliTier.TIER_2,
        scopes=frozenset({PermissionScope.CAN_VULN_SCAN}),
        default_timeout=120,
        description="Windows/SMB/Samba enumeration",
    ),

    # ── TIER 3: Exploitation / Intrusive ──────────────────────────────────
    "hydra": KaliToolMeta(
        name="hydra", binary="hydra",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_BRUTEFORCE}),
        default_timeout=600,
        description="Network login brute-forcer",
    ),
    "john": KaliToolMeta(
        name="john", binary="john",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_BRUTEFORCE}),
        default_timeout=600,
        description="Password hash cracker",
    ),
    "hashcat": KaliToolMeta(
        name="hashcat", binary="hashcat",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_BRUTEFORCE}),
        default_timeout=900,
        description="GPU-accelerated password recovery",
    ),
    "sqlmap": KaliToolMeta(
        name="sqlmap", binary="sqlmap",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_EXPLOIT}),
        default_timeout=600,
        description="Automated SQL injection and database takeover",
    ),
    "msfconsole": KaliToolMeta(
        name="msfconsole", binary="msfconsole",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_EXPLOIT}),
        default_timeout=900,
        description="Metasploit Framework console",
    ),
    "evil_winrm": KaliToolMeta(
        name="evil_winrm", binary="evil-winrm",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_EXPLOIT}),
        default_timeout=300,
        description="WinRM shell for lateral movement",
    ),
    "crackmapexec": KaliToolMeta(
        name="crackmapexec", binary="crackmapexec",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_EXPLOIT}),
        default_timeout=300,
        description="Network pentesting post-exploitation framework",
    ),
    "responder": KaliToolMeta(
        name="responder", binary="responder",
        tier=KaliTier.TIER_3,
        scopes=frozenset({PermissionScope.CAN_EXPLOIT}),
        default_timeout=300,
        description="LLMNR/NBT-NS/mDNS poisoner",
    ),
}


# ─── Target Scope Validator ──────────────────────────────────────────────────

class TargetScopeValidator:
    """
    Enforces target allowlist from ~/.buddy/kali_targets.json.
    localhost/127.0.0.1/::1 are pre-authorized by default.
    """

    def __init__(self, targets_file: Path | None = None):
        self._file = targets_file or TARGETS_FILE
        self._allowed: set[str] = set()
        self._load()

    def _load(self) -> None:
        """Load allowlist from disk. Creates default if missing."""
        if self._file.exists():
            try:
                data = json.loads(self._file.read_text(encoding="utf-8"))
                self._allowed = set(data.get("allowed_targets", []))
            except (json.JSONDecodeError, OSError):
                self._allowed = set()
        else:
            # Create default config with pre-authorized targets
            self._file.parent.mkdir(parents=True, exist_ok=True)
            default = {
                "allowed_targets": sorted(_PRE_AUTHORIZED),
                "_comment": "Add IPs, domains, or CIDR ranges that B.U.D.D.Y is allowed to scan",
            }
            self._file.write_text(json.dumps(default, indent=2), encoding="utf-8")
            self._allowed = set(_PRE_AUTHORIZED)

    @property
    def allowed_targets(self) -> frozenset[str]:
        return frozenset(self._allowed | _PRE_AUTHORIZED)

    def is_authorized(self, target: str) -> bool:
        """Check if a target is in the allowlist."""
        target = target.strip().lower()

        # Pre-authorized always pass
        if target in _PRE_AUTHORIZED:
            return True

        # Direct match
        if target in self._allowed:
            return True

        # CIDR match (basic: check if target starts with any allowed prefix)
        for allowed in self._allowed:
            if "/" in allowed:
                prefix = allowed.split("/")[0]
                if target.startswith(prefix.rsplit(".", 1)[0]):
                    return True

        return False

    def add_target(self, target: str) -> None:
        """Add a target to the allowlist and persist."""
        self._allowed.add(target.strip().lower())
        self._persist()

    def remove_target(self, target: str) -> None:
        """Remove a target from the allowlist and persist."""
        self._allowed.discard(target.strip().lower())
        self._persist()

    def _persist(self) -> None:
        """Write current allowlist to disk."""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "allowed_targets": sorted(self._allowed | _PRE_AUTHORIZED),
            "_comment": "Add IPs, domains, or CIDR ranges that B.U.D.D.Y is allowed to scan",
        }
        self._file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def reload(self) -> None:
        """Reload from disk."""
        self._load()


# ─── Output Truncation ───────────────────────────────────────────────────────

def _truncate_output(raw: str, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    """Cap output at max_bytes. Append truncation notice if needed."""
    encoded = raw.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return raw
    truncated = encoded[:max_bytes].decode("utf-8", errors="replace")
    return truncated + f"\n\n[OUTPUT TRUNCATED — {len(encoded):,} bytes total, showing first {max_bytes:,}]"


# ─── Target Extraction ───────────────────────────────────────────────────────

_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")
_DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b")


def _extract_targets(args: str) -> list[str]:
    """Extract IPs, CIDRs, and domains from a command argument string."""
    targets: list[str] = []
    targets.extend(_IP_RE.findall(args))
    targets.extend(_DOMAIN_RE.findall(args))
    return targets


# ─── Kali Adapter ─────────────────────────────────────────────────────────────

class KaliAdapter:
    """
    Governed Kali tool execution adapter.

    Usage:
        adapter = KaliAdapter()
        result = adapter.execute("nmap_discovery", "-sV -p 1-1000 127.0.0.1")

    Features:
        - Target scope validation (allowlist enforcement)
        - Per-tool risk tier classification
        - Output capping at 1 MB
        - Timeout enforcement
        - Confidence-based parallel/sequential execution
        - Full journaling integration
    """

    def __init__(
        self,
        targets_file: Path | None = None,
        wsl_distro: str = WSL_DISTRO,
    ):
        self._validator = TargetScopeValidator(targets_file)
        self._distro = wsl_distro

    @property
    def validator(self) -> TargetScopeValidator:
        return self._validator

    def get_tool_meta(self, tool_name: str) -> KaliToolMeta | None:
        """Look up tool metadata from the registry."""
        return KALI_TOOL_REGISTRY.get(tool_name)

    def get_required_scopes(self, tool_name: str) -> frozenset[PermissionScope]:
        """Return the permission scopes required for a tool."""
        meta = self.get_tool_meta(tool_name)
        if not meta:
            return frozenset()
        return meta.scopes

    def validate_targets(self, args: str) -> tuple[bool, list[str]]:
        """
        Validate all targets found in args against the allowlist.
        Returns (all_valid, list_of_unauthorized_targets).
        """
        targets = _extract_targets(args)
        unauthorized = [t for t in targets if not self._validator.is_authorized(t)]
        return (len(unauthorized) == 0), unauthorized

    def execute(
        self,
        tool_name: str,
        args: str,
        timeout: int | None = None,
    ) -> ActionResult:
        """
        Execute a Kali tool through WSL with full governance.

        Steps:
          1. Validate tool exists in registry
          2. Validate targets against allowlist
          3. Build WSL command
          4. Execute with timeout
          5. Cap output at 1 MB
          6. Return structured ActionResult
        """
        # 1. Tool lookup
        meta = self.get_tool_meta(tool_name)
        if not meta:
            return ActionResult(
                status="error",
                summary=f"Unknown Kali tool: {tool_name}. Available: {', '.join(sorted(KALI_TOOL_REGISTRY))}",
            )

        # 2. Target validation
        valid, unauthorized = self.validate_targets(args)
        if not valid:
            return ActionResult(
                status="failure",
                summary=(
                    f"Target scope violation — unauthorized targets: {unauthorized}. "
                    f"Add to ~/.buddy/kali_targets.json or use 'buddy allow-target <ip/domain>'."
                ),
            )

        # 3. Build command
        effective_timeout = timeout or meta.default_timeout
        wsl_cmd = self._build_wsl_command(meta.binary, args)

        # 4. Execute
        try:
            start_ts = time.monotonic()
            proc = subprocess.run(
                wsl_cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                encoding="utf-8",
                errors="replace",
            )
            elapsed = time.monotonic() - start_ts

            # 5. Cap output
            stdout = _truncate_output(proc.stdout or "")
            stderr = _truncate_output(proc.stderr or "")

            if proc.returncode == 0:
                return ActionResult(
                    status="success",
                    summary=f"[{meta.name}] completed in {elapsed:.1f}s (exit 0)",
                    artifacts=[],
                    observations={
                        "tool": meta.name,
                        "tier": meta.tier.value,
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": 0,
                        "elapsed_seconds": round(elapsed, 2),
                    },
                )
            else:
                return ActionResult(
                    status="failure",
                    summary=f"[{meta.name}] exited with code {proc.returncode} after {elapsed:.1f}s",
                    observations={
                        "tool": meta.name,
                        "tier": meta.tier.value,
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": proc.returncode,
                        "elapsed_seconds": round(elapsed, 2),
                    },
                )

        except subprocess.TimeoutExpired:
            return ActionResult(
                status="error",
                summary=f"[{meta.name}] timed out after {effective_timeout}s",
                observations={"tool": meta.name, "timeout": effective_timeout},
            )
        except FileNotFoundError:
            return ActionResult(
                status="error",
                summary=f"WSL not found or distro '{self._distro}' not available. Is Kali installed?",
            )
        except OSError as exc:
            return ActionResult(
                status="error",
                summary=f"[{meta.name}] OS error: {exc}",
            )

    def execute_parallel(
        self,
        commands: list[tuple[str, str]],
        timeout: int | None = None,
    ) -> list[ActionResult]:
        """
        Execute multiple Kali tools in parallel (for high-confidence batches).

        Args:
            commands: List of (tool_name, args) tuples
            timeout: Per-command timeout override

        Returns:
            List of ActionResults in same order as commands
        """
        import concurrent.futures

        results: list[ActionResult] = [None] * len(commands)  # type: ignore

        def _run(idx: int, tool_name: str, args: str) -> tuple[int, ActionResult]:
            return idx, self.execute(tool_name, args, timeout=timeout)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(_run, i, tn, a)
                for i, (tn, a) in enumerate(commands)
            ]
            for future in concurrent.futures.as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        return results

    def _build_wsl_command(self, binary: str, args: str) -> list[str]:
        """Build the WSL command list for subprocess."""
        return [
            "wsl", "-d", self._distro, "--",
            "bash", "-c", f"{binary} {args}"
        ]

    def list_available_tools(self) -> dict[str, list[str]]:
        """Return tools grouped by tier."""
        grouped: dict[str, list[str]] = {
            KaliTier.TIER_1.value: [],
            KaliTier.TIER_2.value: [],
            KaliTier.TIER_3.value: [],
        }
        for name, meta in sorted(KALI_TOOL_REGISTRY.items()):
            grouped[meta.tier.value].append(f"{name} ({meta.description})")
        return grouped


# ─── Executor Integration Helper ─────────────────────────────────────────────

def kali_tool(parameters: dict, speak=None, **kw) -> str:
    """
    Entry point for the executor tool registry.
    Expected parameters:
        tool: str       — Kali tool name from KALI_TOOL_REGISTRY
        args: str       — Arguments to pass to the tool
        timeout: int    — Optional timeout override
    """
    tool_name = parameters.get("tool", "")
    args = parameters.get("args", "")
    timeout = parameters.get("timeout")

    adapter = KaliAdapter()
    result = adapter.execute(tool_name, args, timeout=timeout)

    if speak and result.status != "success":
        speak(f"Kali tool issue: {result.summary}")

    # Return structured output for the runtime
    if result.observations and result.observations.get("stdout"):
        return f"[{result.status}] {result.summary}\n\n{result.observations['stdout']}"
    return f"[{result.status}] {result.summary}"
