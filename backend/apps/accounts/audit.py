from __future__ import annotations

from typing import Any

from apps.accounts.models import AuditLog


SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "authorization"}


def write_audit_log(user, *, action: str, object_type: str, object_id: str | int = "", metadata: dict[str, Any] | None = None):
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id or ""),
        metadata=_redact_metadata(metadata or {}),
    )


def _redact_metadata(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else _redact_metadata(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_metadata(item) for item in value]
    return value
