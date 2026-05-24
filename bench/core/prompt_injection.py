from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bench.core.normalization import normalize_text
from bench.core.policy_engine import LocalPolicyEngine, load_default_policy_engine


@dataclass(frozen=True)
class InjectionFinding:
    type: str
    severity: str
    matched_rule_id: str
    action: str
    evidence_redacted: str
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PromptInjectionDetector:
    def __init__(self, policy_engine: LocalPolicyEngine | None = None, normalization_cfg=None):
        self.policy_engine = policy_engine or load_default_policy_engine()
        self.normalization_cfg = normalization_cfg

    def detect(self, raw_text: str, normalized_text: str | None = None) -> list[InjectionFinding]:
        normalized = normalized_text
        if normalized is None:
            normalized = normalize_text(raw_text, self.normalization_cfg).normalized
        decisions = self.policy_engine.evaluate(
            raw_text=raw_text or "",
            normalized_text=normalized or "",
            stage="input",
        )
        findings = []
        for decision in decisions:
            if decision.detector_type != "prompt_injection":
                continue
            findings.append(
                InjectionFinding(
                    type=decision.detector_type,
                    severity=decision.severity,
                    matched_rule_id=decision.rule_id,
                    action=decision.action,
                    evidence_redacted=decision.evidence_redacted,
                    tags=decision.tags,
                )
            )
        return findings
