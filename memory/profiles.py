from __future__ import annotations

from pathlib import Path

from memory.schema import MemoryTier, MemorySensitivity, PROFILE_TIERS, SECRET_SENSITIVITY


class ProfileManager:
    _DEFAULT_USER = """# User Profile

## Identity

## Goals

## Skills

## Projects

## Career Targets

## Communication Preferences

## Platform Links

## Consent Approval Preferences
"""
    _DEFAULT_SOUL = """# BUDDY Soul

## Purpose
- purpose: assist the user with reliable local-device and professional workflows

## Tone
- tone: refined, helpful, direct

## Safety Boundaries
- external_actions: require approval before submission
"""
    _DEFAULT_HEARTBEAT = """# BUDDY Heartbeat

## Runtime State
- status: idle
"""

    def __init__(self, profiles_dir: Path):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.user_path = self.profiles_dir / "user.md"
        self.soul_path = self.profiles_dir / "soul.md"
        self.heartbeat_path = self.profiles_dir / "heartbeat.md"
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if not self.user_path.exists():
            self.user_path.write_text(self._DEFAULT_USER, encoding="utf-8")
        if not self.soul_path.exists():
            self.soul_path.write_text(self._DEFAULT_SOUL, encoding="utf-8")
        if not self.heartbeat_path.exists():
            self.heartbeat_path.write_text(self._DEFAULT_HEARTBEAT, encoding="utf-8")

    def load_user_context(self) -> str:
        return self.user_path.read_text(encoding="utf-8")

    def load_soul_context(self) -> str:
        return self.soul_path.read_text(encoding="utf-8")

    def update_user(
        self,
        category: str,
        key: str,
        value: str,
        tier: MemoryTier = MemoryTier.LONG_TERM,
        sensitivity: MemorySensitivity = MemorySensitivity.NORMAL,
    ) -> None:
        """Write to user.md only if tier is PREFERENCE or LONG_TERM and not SECRET."""
        # SECRET entries must never reach the profile file
        if sensitivity == SECRET_SENSITIVITY:
            return
        # Only PREFERENCE and LONG_TERM tiers write to user.md
        if tier not in PROFILE_TIERS:
            return

        section_title = self._section_title(category)
        content = self.user_path.read_text(encoding="utf-8")

        # Redact any value that looks like a secret (belt-and-suspenders)
        safe_value = self._redact_if_suspicious(value)
        content = self._upsert_bullet(content, section_title, key, safe_value)
        self._atomic_write(self.user_path, content)

    def write_heartbeat(self, status: dict) -> None:
        lines = ["# BUDDY Heartbeat", "", "## Runtime State"]
        for key, value in status.items():
            lines.append(f"- {key}: {value}")
        self._atomic_write(self.heartbeat_path, "\n".join(lines) + "\n")

    @staticmethod
    def _section_title(category: str) -> str:
        return category.replace("_", " ").title()

    @staticmethod
    def _redact_if_suspicious(value: str) -> str:
        """Redact values that look like API keys, tokens, or passwords."""
        lower = value.lower().strip()
        # Common secret prefixes
        secret_prefixes = ("sk-", "pk-", "ghp_", "gho_", "xoxb-", "xoxp-", "bearer ")
        if any(lower.startswith(p) for p in secret_prefixes):
            return "[REDACTED]"
        # Very long hex/base64 strings that look like tokens
        if len(value) > 40 and value.replace("-", "").replace("_", "").isalnum():
            return "[REDACTED]"
        return value

    def _upsert_bullet(self, content: str, section_title: str, key: str, value: str) -> str:
        header = f"## {section_title}"
        if header not in content:
            content = content.rstrip() + f"\n\n{header}\n- {key}: {value}\n"
            return content

        lines = content.splitlines()
        output: list[str] = []
        in_section = False
        updated = False
        for idx, line in enumerate(lines):
            if line == header:
                in_section = True
                output.append(line)
                continue
            if in_section and line.startswith("## "):
                if not updated:
                    output.append(f"- {key}: {value}")
                    updated = True
                in_section = False
            if in_section and line.startswith(f"- {key}:"):
                output.append(f"- {key}: {value}")
                updated = True
                continue
            output.append(line)

        if in_section and not updated:
            output.append(f"- {key}: {value}")
        return "\n".join(output).rstrip() + "\n"

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(path)
