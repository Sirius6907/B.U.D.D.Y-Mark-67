from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from registries.aliases import AliasIndex
from registries.domain_index import DomainIndex
from registries.tool_manifest import ToolManifest

# ── Maturity ordering for planner preference ──
_MATURITY_RANK = {"core": 0, "stable": 1, "experimental": 2}
_LATENCY_RANK = {"fast": 0, "medium": 1, "slow": 2}


@dataclass(frozen=True)
class CapabilitySpec:
    tool_name: str
    domain: str = "generic"
    operation: str = "run"
    aliases: tuple[str, ...] = ()
    risk_level: str = "LOW"
    idempotent: bool = False
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    verification_mode: str = "not_applicable"
    # ── Phase 3 quality metadata ──
    reliability_score: float = 0.5          # 0–1, higher = more reliable
    verification_supported: bool = False    # True if tool produces verifiable state
    maturity_level: str = "experimental"    # "core" | "stable" | "experimental"
    latency_class: str = "medium"           # "fast" | "medium" | "slow"
    requires_ui_focus: bool = False         # True if tool needs active UI focus

    def __post_init__(self) -> None:
        object.__setattr__(self, "aliases", self._normalize_sequence("aliases", self.aliases))
        object.__setattr__(
            self, "preconditions", self._normalize_sequence("preconditions", self.preconditions)
        )
        object.__setattr__(
            self, "postconditions", self._normalize_sequence("postconditions", self.postconditions)
        )

    @staticmethod
    def _normalize_sequence(field_name: str, value: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        if isinstance(value, str):
            raise TypeError(f"{field_name} must be a sequence of strings, not a scalar string")
        normalized = tuple(value)
        if not all(isinstance(item, str) for item in normalized):
            raise TypeError(f"{field_name} must contain only strings")
        return normalized


class CapabilityRegistry:
    def __init__(self) -> None:
        self._manifest = ToolManifest()
        self._domains = DomainIndex()
        self._aliases = AliasIndex()

    def register(self, spec: CapabilitySpec) -> None:
        previous = self._manifest.add(spec.tool_name, spec)
        if isinstance(previous, CapabilitySpec):
            self._domains.remove(previous.domain, previous.tool_name)
            for alias in previous.aliases:
                self._aliases.remove(alias, previous.tool_name)
        self._domains.add(spec.domain, spec.tool_name)
        for alias in spec.aliases:
            self._aliases.add(alias, spec.tool_name)

    def find_by_alias(self, alias: str) -> list[CapabilitySpec]:
        return [
            spec
            for tool_name in self._aliases.get(alias)
            if (spec := self._manifest.get(tool_name)) is not None
        ]

    def list_domain(self, domain: str) -> list[CapabilitySpec]:
        return [
            spec
            for tool_name in self._domains.get(domain)
            if (spec := self._manifest.get(tool_name)) is not None
        ]

    def get(self, tool_name: str) -> CapabilitySpec | None:
        spec = self._manifest.get(tool_name)
        return spec if isinstance(spec, CapabilitySpec) else None

    # ── Phase 3: Quality-ranked selection ──

    @staticmethod
    def _quality_sort_key(spec: CapabilitySpec) -> tuple:
        """Sort key: prefer core > stable > experimental,
        verified > non-verified, higher reliability, faster latency."""
        return (
            _MATURITY_RANK.get(spec.maturity_level, 99),
            0 if spec.verification_supported else 1,
            -spec.reliability_score,  # negative so higher is first
            _LATENCY_RANK.get(spec.latency_class, 99),
        )

    def ranked_by_quality(self, specs: list[CapabilitySpec]) -> list[CapabilitySpec]:
        """Return specs sorted by quality preference (best first)."""
        return sorted(specs, key=self._quality_sort_key)

    def find_by_capability(self, domain: str, operation: Optional[str] = None) -> list[CapabilitySpec]:
        """Find tools by domain+operation, ranked by quality.

        If operation is given, filters to matching operation.
        Always returns quality-ranked results.
        """
        specs = self.list_domain(domain)
        if operation:
            specs = [s for s in specs if s.operation == operation]
        return self.ranked_by_quality(specs)

    def resolve_with_quality(self, tool_name: str) -> Optional[CapabilitySpec]:
        """Resolve a tool name (or alias), returning the best-quality match.

        Resolution order:
        1. Direct name match
        2. Alias lookup (returns highest-quality match)
        """
        # Direct lookup
        spec = self.get(tool_name)
        if spec is not None:
            return spec

        # Legacy alias resolution
        from registries.legacy_aliases import resolve_alias
        resolved = resolve_alias(tool_name)
        if resolved != tool_name:
            spec = self.get(resolved)
            if spec is not None:
                return spec

        # Registry alias lookup (return best quality)
        matches = self.find_by_alias(tool_name)
        if matches:
            return self.ranked_by_quality(matches)[0]

        return None
