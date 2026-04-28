"""
agent/safety.py — Content Safety Scanner
==========================================
Pre-execution adversarial input scanner that detects:
  • Prompt injection attempts (goal hijacking, role override)
  • Path traversal attacks (../../ escapes, UNC paths)
  • Data exfiltration vectors (curl/wget piped to external hosts)
  • Command injection patterns (shell metacharacters, chained commands)
  • Credential exposure (hardcoded keys, tokens in arguments)

The scanner returns a ScanResult before each tool execution.
If threats are detected, the runtime can block or require approval.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ThreatCategory(str, Enum):
    """Classification of detected threats."""
    SAFE              = "safe"
    PROMPT_INJECTION  = "prompt_injection"
    PATH_TRAVERSAL    = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    CREDENTIAL_LEAK   = "credential_leak"
    KALI_UNSAFE       = "kali_unsafe"


class ThreatSeverity(str, Enum):
    """How severe the detected threat is."""
    NONE     = "none"
    LOW      = "low"       # suspicious but likely benign
    MEDIUM   = "medium"    # probable attack pattern
    HIGH     = "high"      # confirmed dangerous pattern
    CRITICAL = "critical"  # active exploit attempt


@dataclass(slots=True)
class ThreatSignal:
    """A single detected threat signal."""
    category: ThreatCategory
    severity: ThreatSeverity
    pattern: str           # what matched
    evidence: str          # the matching text fragment
    description: str       # human-readable explanation


@dataclass(slots=True)
class ScanResult:
    """Aggregated result of scanning an input."""
    safe: bool
    max_severity: ThreatSeverity
    signals: list[ThreatSignal] = field(default_factory=list)
    scanned_text: str = ""
    scan_time_ms: float = 0.0

    @property
    def blocked(self) -> bool:
        """Should execution be blocked?"""
        return self.max_severity in (ThreatSeverity.HIGH, ThreatSeverity.CRITICAL)

    @property
    def needs_approval(self) -> bool:
        """Should the user approve before proceeding?"""
        return self.max_severity == ThreatSeverity.MEDIUM

    def summary(self) -> str:
        if self.safe:
            return "No threats detected"
        cats = {s.category.value for s in self.signals}
        return f"{len(self.signals)} threat(s) detected: {', '.join(sorted(cats))}"


# ─── Pattern Definitions ─────────────────────────────────────────────────

# Prompt injection patterns — attempts to override instructions
_INJECTION_PATTERNS: list[tuple[re.Pattern, ThreatSeverity, str]] = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|prompts?)",
                re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Goal hijacking: attempts to override prior instructions"),

    (re.compile(r"you\s+are\s+now\s+(a|an|the)\s+\w+",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Role override: attempts to redefine agent identity"),

    (re.compile(r"(system\s*prompt|system\s*message)\s*[:=]",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "System prompt injection attempt"),

    (re.compile(r"forget\s+(everything|all|what)\s+(you|i)\s+(told|said|know)",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Memory wipe: attempts to erase context"),

    (re.compile(r"<\s*(system|assistant|user)\s*>",
                re.IGNORECASE),
     ThreatSeverity.MEDIUM,
     "Chat role tag injection"),

    (re.compile(r"do\s+not\s+follow\s+(any\s+)?(safety|security|content)\s+(guidelines?|rules?|policies?)",
                re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Safety bypass: attempts to disable safety rules"),

    (re.compile(r"pretend\s+(you|that)\s+(are|you're|can|have)\s+no\s+(restrictions?|limits?|filters?)",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Restriction bypass via roleplay"),
]

# Path traversal patterns
_TRAVERSAL_PATTERNS: list[tuple[re.Pattern, ThreatSeverity, str]] = [
    (re.compile(r"\.\.[/\\]"),
     ThreatSeverity.HIGH,
     "Directory traversal: ../ or ..\\ escape sequence"),

    (re.compile(r"[/\\](etc|proc|sys|dev|boot|root)[/\\]",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Sensitive system directory access"),

    (re.compile(r"\\\\[a-zA-Z0-9_.\-]+\\",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "UNC path: potential network share access"),

    (re.compile(r"[A-Z]:\\(Windows|Program\s*Files|System32)",
                re.IGNORECASE),
     ThreatSeverity.MEDIUM,
     "Windows system directory access attempt"),

    (re.compile(r"~[/\\]\.(ssh|gnupg|aws|config|bashrc|profile)",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Home directory sensitive file access"),
]

# Command injection patterns
_COMMAND_INJECTION_PATTERNS: list[tuple[re.Pattern, ThreatSeverity, str]] = [
    (re.compile(r"[;&|]\s*(rm|del|format|mkfs|dd)\s",
                re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Destructive command chaining"),

    (re.compile(r"`[^`]+`"),
     ThreatSeverity.MEDIUM,
     "Backtick command substitution"),

    (re.compile(r"\$\([^)]+\)"),
     ThreatSeverity.MEDIUM,
     "Shell command substitution $()"),

    (re.compile(r"[|]\s*(bash|sh|cmd|powershell|pwsh)\b",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Pipe to shell interpreter"),

    (re.compile(r">\s*/dev/sd[a-z]",
                re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Direct write to block device"),

    (re.compile(r"(chmod|chown)\s+.*777",
                re.IGNORECASE),
     ThreatSeverity.MEDIUM,
     "Overly permissive file permission change"),
]

# Data exfiltration patterns
_EXFIL_PATTERNS: list[tuple[re.Pattern, ThreatSeverity, str]] = [
    (re.compile(r"(curl|wget|invoke-webrequest|iwr)\s+.*https?://",
                re.IGNORECASE),
     ThreatSeverity.MEDIUM,
     "HTTP tool invocation with external URL"),

    (re.compile(r"(curl|wget)\s+.*(-d|--data|--upload-file)\s",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Data upload via command-line tool"),

    (re.compile(r"(nc|ncat|netcat)\s+.*\d+\.\d+\.\d+\.\d+",
                re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Netcat connection to external IP"),

    (re.compile(r"base64\s.*[|>]",
                re.IGNORECASE),
     ThreatSeverity.MEDIUM,
     "Base64 encoding piped to output (potential data encoding for exfil)"),

    (re.compile(r"(scp|rsync|ftp)\s+.*@",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "File transfer to remote host"),
]

# Credential leak patterns
_CREDENTIAL_PATTERNS: list[tuple[re.Pattern, ThreatSeverity, str]] = [
    (re.compile(r"(api[_-]?key|api[_-]?secret|access[_-]?token|auth[_-]?token)\s*[=:]\s*['\"]?[A-Za-z0-9+/=_-]{16,}",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Potential API key or token in plaintext"),

    (re.compile(r"(password|passwd|pwd)\s*[=:]\s*['\"]?[^\s'\"]{6,}",
                re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Potential password in plaintext"),

    (re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
                re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Private key detected in input"),

    (re.compile(r"AWS[A-Za-z]*[=:]\s*['\"]?AKIA[A-Z0-9]{16}",
                re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "AWS access key detected"),

    (re.compile(r"(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{36,}"),
     ThreatSeverity.HIGH,
     "GitHub token detected"),
]

# Kali tool argument safety patterns
_KALI_DANGEROUS_PATTERNS: list[tuple[re.Pattern, ThreatSeverity, str]] = [
    (re.compile(r"0\.0\.0\.0/0|::/0|\*\.\*\.\*\.\*", re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Wildcard network scan target — blocks entire internet scanning"),

    (re.compile(r"--os-pwn|--os-shell|--priv-esc", re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "SQLMap exploitation flag detected"),

    (re.compile(r"exploit/.*(?:exec|shell|reverse|bind)", re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Metasploit exploitation module detected"),

    (re.compile(r"-e\s+(cmd|bash|sh|powershell)", re.IGNORECASE),
     ThreatSeverity.HIGH,
     "Reverse shell execution flag"),

    (re.compile(r"--batch\s+--dump-all", re.IGNORECASE),
     ThreatSeverity.HIGH,
     "SQLMap full database dump in batch mode"),

    (re.compile(r"meterpreter|reverse_tcp|bind_tcp|reverse_https", re.IGNORECASE),
     ThreatSeverity.CRITICAL,
     "Meterpreter/reverse shell payload reference"),
]

# All pattern groups
_ALL_PATTERN_GROUPS: list[tuple[ThreatCategory, list]] = [
    (ThreatCategory.PROMPT_INJECTION,  _INJECTION_PATTERNS),
    (ThreatCategory.PATH_TRAVERSAL,    _TRAVERSAL_PATTERNS),
    (ThreatCategory.COMMAND_INJECTION, _COMMAND_INJECTION_PATTERNS),
    (ThreatCategory.DATA_EXFILTRATION, _EXFIL_PATTERNS),
    (ThreatCategory.CREDENTIAL_LEAK,   _CREDENTIAL_PATTERNS),
    (ThreatCategory.KALI_UNSAFE,       _KALI_DANGEROUS_PATTERNS),
]


# ─── Severity Ordering ───────────────────────────────────────────────────

_SEVERITY_ORDER = {
    ThreatSeverity.NONE: 0,
    ThreatSeverity.LOW: 1,
    ThreatSeverity.MEDIUM: 2,
    ThreatSeverity.HIGH: 3,
    ThreatSeverity.CRITICAL: 4,
}


def _max_severity(a: ThreatSeverity, b: ThreatSeverity) -> ThreatSeverity:
    return a if _SEVERITY_ORDER[a] >= _SEVERITY_ORDER[b] else b


# ─── Content Safety Scanner ──────────────────────────────────────────────

class ContentSafetyScanner:
    """
    Scans tool arguments, prompts, and user inputs for adversarial content.

    Usage:
        scanner = ContentSafetyScanner()
        result = scanner.scan("rm -rf / && curl evil.com")
        if result.blocked:
            raise SecurityError(result.summary())
    """

    def __init__(self, *, extra_patterns: list[tuple[ThreatCategory, re.Pattern, ThreatSeverity, str]] | None = None):
        """
        Args:
            extra_patterns: Additional (category, pattern, severity, description) tuples
                           for project-specific threat detection.
        """
        self._extra: list[tuple[ThreatCategory, re.Pattern, ThreatSeverity, str]] = extra_patterns or []
        self._scan_count: int = 0
        self._block_count: int = 0

    def scan(self, text: str) -> ScanResult:
        """
        Scan text for all known threat patterns.

        Returns a ScanResult with signals for each match.
        """
        import time as _time
        t0 = _time.monotonic()
        self._scan_count += 1

        signals: list[ThreatSignal] = []
        max_sev = ThreatSeverity.NONE

        # Scan all built-in pattern groups
        for category, patterns in _ALL_PATTERN_GROUPS:
            for pat, severity, desc in patterns:
                match = pat.search(text)
                if match:
                    signal = ThreatSignal(
                        category=category,
                        severity=severity,
                        pattern=pat.pattern,
                        evidence=match.group()[:100],  # cap evidence length
                        description=desc,
                    )
                    signals.append(signal)
                    max_sev = _max_severity(max_sev, severity)

        # Scan extra patterns
        for category, pat, severity, desc in self._extra:
            match = pat.search(text)
            if match:
                signal = ThreatSignal(
                    category=category,
                    severity=severity,
                    pattern=pat.pattern,
                    evidence=match.group()[:100],
                    description=desc,
                )
                signals.append(signal)
                max_sev = _max_severity(max_sev, severity)

        elapsed_ms = (_time.monotonic() - t0) * 1000
        safe = max_sev in (ThreatSeverity.NONE, ThreatSeverity.LOW)

        result = ScanResult(
            safe=safe,
            max_severity=max_sev,
            signals=signals,
            scanned_text=text[:200] + ("..." if len(text) > 200 else ""),
            scan_time_ms=round(elapsed_ms, 3),
        )

        if result.blocked:
            self._block_count += 1

        return result

    def scan_args(self, args: dict[str, Any]) -> ScanResult:
        """
        Scan tool arguments dict — concatenates all string values
        and scans as a single block.
        """
        parts: list[str] = []
        for key, val in args.items():
            if isinstance(val, str):
                parts.append(val)
            elif isinstance(val, list):
                parts.extend(str(v) for v in val if isinstance(v, str))
        combined = " ".join(parts)
        return self.scan(combined)

    def scan_node(self, tool: str, args: dict[str, Any], objective: str = "") -> ScanResult:
        """
        Full scan of a task node: tool name + args + objective.
        """
        combined = f"{tool} {objective} " + " ".join(
            str(v) for v in args.values() if isinstance(v, str)
        )
        return self.scan(combined)

    @property
    def stats(self) -> dict[str, int]:
        return {
            "scans": self._scan_count,
            "blocks": self._block_count,
        }

    def reset_stats(self) -> None:
        self._scan_count = 0
        self._block_count = 0
