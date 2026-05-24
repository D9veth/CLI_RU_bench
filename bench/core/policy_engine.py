from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from bench.core.paths import find_repo_root, resolve_config_path


@dataclass(frozen=True)
class PolicyDecision:
    allow: bool
    action: str
    reason: str
    rule_id: str
    severity: str
    tags: list[str]
    stage: str
    detector_type: str
    evidence_redacted: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LocalPolicyEngine:
    def __init__(self, rules: list[dict[str, Any]], *, version: str = "local"):
        self.rules = [rule for rule in rules if rule.get("enabled", True)]
        self.version = version
        self.rules_hash = hashlib.sha256(
            yaml.safe_dump(self.rules, allow_unicode=True, sort_keys=True).encode("utf-8")
        ).hexdigest()

    @classmethod
    def from_paths(cls, paths: list[str | Path], *, config_dir: Path | None = None) -> "LocalPolicyEngine":
        rules: list[dict[str, Any]] = []
        resolved_paths: list[Path] = []
        repo_root = find_repo_root(config_dir or Path.cwd())
        for path in paths:
            resolved = resolve_config_path(
                path,
                config_dir=config_dir,
                repo_root=repo_root,
                label="policy rules path",
            )
            resolved_paths.append(resolved)
            payload = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
            loaded_rules = payload.get("rules", payload if isinstance(payload, list) else [])
            if not isinstance(loaded_rules, list):
                raise ValueError(f"Policy rules must be a list in {resolved}")
            rules.extend(rule for rule in loaded_rules if isinstance(rule, dict))
        version = "+".join(path.name for path in resolved_paths) or "local"
        return cls(rules, version=version)

    def evaluate(self, *, raw_text: str, normalized_text: str, stage: str) -> list[PolicyDecision]:
        decisions: list[PolicyDecision] = []
        for rule in self.rules:
            applies_to = set(rule.get("applies_to") or [])
            if applies_to and stage not in applies_to:
                continue
            pattern = str(rule.get("pattern") or "")
            if not pattern:
                continue
            flags = 0 if rule.get("case_sensitive") else re.IGNORECASE
            haystacks = [normalized_text or "", raw_text or ""]
            for text in haystacks:
                match = re.search(pattern, text, flags=flags)
                if not match:
                    continue
                action = str(rule.get("action") or "audit").lower()
                decisions.append(
                    PolicyDecision(
                        allow=action in {"allow", "audit"},
                        action=action,
                        reason=str(rule.get("reason") or rule.get("description") or rule.get("rule_id") or ""),
                        rule_id=str(rule.get("rule_id") or "unnamed_rule"),
                        severity=str(rule.get("severity") or "medium"),
                        tags=[str(tag) for tag in rule.get("tags", [])],
                        stage=stage,
                        detector_type=str(rule.get("detector_type") or "regex"),
                        evidence_redacted=_redact_evidence(match.group(0)),
                    )
                )
                break
        return decisions


def load_default_policy_engine(config_dir: Path | None = None) -> LocalPolicyEngine:
    return LocalPolicyEngine.from_paths(["policies/rules/ru_guardrails.yaml"], config_dir=config_dir)


def _redact_evidence(value: str) -> str:
    value = value or ""
    if len(value) <= 8:
        return "[redacted]"
    return f"{value[:3]}...[redacted]...{value[-2:]}"
