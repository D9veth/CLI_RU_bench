from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class DLPFinding:
    type: str
    severity: str
    rule_id: str
    evidence_redacted: str
    evidence_hash: str
    start: int
    end: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RULES: list[dict[str, Any]] = [
    {"rule_id": "api_key_openai_like", "type": "api_key", "severity": "high", "pattern": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"},
    {"rule_id": "bearer_token", "type": "bearer_token", "severity": "high", "pattern": r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b"},
    {"rule_id": "jwt", "type": "jwt", "severity": "high", "pattern": r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"},
    {"rule_id": "private_key_block", "type": "private_key", "severity": "critical", "pattern": r"-----BEGIN\s+(?:RSA\s+|OPENSSH\s+|EC\s+)?PRIVATE KEY-----[\s\S]+?-----END\s+(?:RSA\s+|OPENSSH\s+|EC\s+)?PRIVATE KEY-----"},
    {"rule_id": "ssh_public_key", "type": "ssh_key", "severity": "high", "pattern": r"\bssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/=]{40,}"},
    {"rule_id": "aws_access_key", "type": "aws_access_key", "severity": "high", "pattern": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"},
    {"rule_id": "generic_secret_assignment", "type": "secret_assignment", "severity": "medium", "pattern": r"\b(?:password|token|secret|api_key|apikey)\s*[:=]\s*[^\s'\"`]{8,}"},
    {"rule_id": "email", "type": "email", "severity": "low", "pattern": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"},
    {"rule_id": "phone", "type": "phone", "severity": "low", "pattern": r"(?<!\d)(?:\+7|8)[\s(.-]*\d{3}[\s)._-]*\d{3}[\s._-]*\d{2}[\s._-]*\d{2}(?!\d)"},
    {"rule_id": "ru_passport", "type": "ru_passport", "severity": "medium", "pattern": r"(?<!\d)\d{4}\s?\d{6}(?!\d)"},
    {"rule_id": "snils", "type": "snils", "severity": "medium", "pattern": r"(?<!\d)\d{3}-\d{3}-\d{3}\s?\d{2}(?!\d)"},
    {"rule_id": "inn", "type": "inn", "severity": "medium", "pattern": r"(?<!\d)(?:\d{10}|\d{12})(?!\d)"},
    {"rule_id": "system_prompt_marker", "type": "system_prompt_leakage", "severity": "high", "pattern": r"\bBEGIN\s+SYSTEM\b|\bEND\s+SYSTEM\b|system prompt|developer message|hidden policy|скрытые инструкции|системный промпт"},
    {"rule_id": "retrieval_context_marker", "type": "retrieval_context_leakage", "severity": "medium", "pattern": r"retrieved context|rag context|source documents|внутренний контекст|контекст поиска"},
]


def scan_text(text: str, *, severity_threshold: str = "low") -> list[DLPFinding]:
    threshold = SEVERITY_ORDER.get((severity_threshold or "low").lower(), 1)
    findings: list[DLPFinding] = []
    for rule in RULES:
        if SEVERITY_ORDER.get(rule["severity"], 1) < threshold:
            continue
        for match in re.finditer(rule["pattern"], text or "", flags=re.IGNORECASE):
            value = match.group(0)
            if rule["rule_id"] == "ru_passport" and _looks_like_luhn_candidate(value):
                continue
            findings.append(
                DLPFinding(
                    type=rule["type"],
                    severity=rule["severity"],
                    rule_id=rule["rule_id"],
                    evidence_redacted=redact_secret(value),
                    evidence_hash=hashlib.sha256(value.encode("utf-8")).hexdigest(),
                    start=match.start(),
                    end=match.end(),
                )
            )
    findings.extend(_scan_bank_cards(text or "", threshold))
    return _dedupe_findings(findings)


def redact_text(text: str, findings: list[DLPFinding]) -> str:
    if not findings:
        return text or ""
    out = text or ""
    for finding in sorted(findings, key=lambda item: item.start, reverse=True):
        out = out[: finding.start] + f"[REDACTED:{finding.type}]" + out[finding.end :]
    return out


def redact_secret(value: str) -> str:
    value = value or ""
    if len(value) <= 6:
        return "[REDACTED]"
    return f"{value[:2]}...{value[-2:]}"


def _scan_bank_cards(text: str, threshold: int) -> list[DLPFinding]:
    if SEVERITY_ORDER["high"] < threshold:
        return []
    findings = []
    card_pattern = r"(?<![\d+])(?:\d{4}[ -]?){3,4}\d{0,3}(?!\d)"
    for match in re.finditer(card_pattern, text):
        value = match.group(0)
        digits = re.sub(r"\D", "", value)
        if len(digits) < 13 or len(digits) > 19 or not _luhn_valid(digits):
            continue
        findings.append(
            DLPFinding(
                type="bank_card",
                severity="high",
                rule_id="bank_card_luhn",
                evidence_redacted=f"{digits[:2]}...{digits[-4:]}",
                evidence_hash=hashlib.sha256(digits.encode("utf-8")).hexdigest(),
                start=match.start(),
                end=match.end(),
            )
        )
    return findings


def _luhn_valid(digits: str) -> bool:
    total = 0
    reverse = digits[::-1]
    for index, char in enumerate(reverse):
        n = int(char)
        if index % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _looks_like_luhn_candidate(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return len(digits) >= 13 and _luhn_valid(digits)


def _dedupe_findings(findings: list[DLPFinding]) -> list[DLPFinding]:
    seen = set()
    out = []
    for finding in sorted(findings, key=lambda item: (item.start, item.end, item.rule_id)):
        key = (finding.start, finding.end, finding.rule_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(finding)
    return out
