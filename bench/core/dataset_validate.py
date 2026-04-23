from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bench.core.dataset import VALID_CASE_TYPES, VALID_ROLES, load_dataset_objects


@dataclass
class ValidationIssue:
    level: str  # "error" | "warning"
    code: str
    index: Optional[int]
    case_id: Optional[str]
    field: Optional[str]
    message: str


@dataclass
class DatasetValidationReport:
    ok: bool
    dataset_path: str
    generated_at: str
    counts: Dict[str, Any]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _qa_like_utility_case(obj: Dict[str, Any]) -> bool:
    task = obj.get("utility_task")
    values: List[str] = []
    if isinstance(task, str):
        values.append(task)
    elif isinstance(task, dict):
        for k in ("name", "task", "suite", "type"):
            v = task.get(k)
            if isinstance(v, str):
                values.append(v)
    category = obj.get("category")
    if isinstance(category, str):
        values.append(category)
    low = " ".join(values).lower()
    return any(token in low for token in ("qa", "squad", "sberquad", "quad"))


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate_dataset_file(path: Path) -> DatasetValidationReport:
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []

    try:
        items = load_dataset_objects(path)
    except Exception as e:
        errors.append(
            ValidationIssue(
                level="error",
                code="dataset_parse_error",
                index=None,
                case_id=None,
                field=None,
                message=str(e),
            )
        )
        return DatasetValidationReport(
            ok=False,
            dataset_path=str(path),
            generated_at=datetime.now(timezone.utc).isoformat(),
            counts={
                "n_items": 0,
                "n_attack": 0,
                "n_benign": 0,
                "n_utility": 0,
                "n_errors": len(errors),
                "n_warnings": len(warnings),
            },
            errors=[asdict(x) for x in errors],
            warnings=[asdict(x) for x in warnings],
        )

    seen_ids: Dict[str, int] = {}
    n_attack = n_benign = n_utility = 0

    def add_issue(level: str, code: str, idx: Optional[int], case_id: Optional[str], field: Optional[str], message: str):
        issue = ValidationIssue(
            level=level,
            code=code,
            index=idx,
            case_id=case_id,
            field=field,
            message=message,
        )
        if level == "error":
            errors.append(issue)
        else:
            warnings.append(issue)

    for idx, obj in enumerate(items):
        case_id = str(obj.get("id")) if obj.get("id") is not None else None

        if not isinstance(obj, dict):
            add_issue("error", "case_not_object", idx, case_id, None, "Dataset item must be an object")
            continue

        # Required fields
        if "id" not in obj:
            add_issue("error", "missing_field", idx, None, "id", "Missing required field: id")
        elif not _nonempty_str(obj.get("id")):
            add_issue("error", "invalid_type", idx, case_id, "id", "Field 'id' must be a non-empty string")

        if "type" not in obj:
            add_issue("error", "missing_field", idx, case_id, "type", "Missing required field: type")
            ctype = None
        else:
            ctype = obj.get("type")
            if not _nonempty_str(ctype):
                add_issue("error", "invalid_type", idx, case_id, "type", "Field 'type' must be a non-empty string")
            elif ctype not in VALID_CASE_TYPES:
                add_issue(
                    "error",
                    "invalid_value",
                    idx,
                    case_id,
                    "type",
                    f"Field 'type' must be one of {sorted(VALID_CASE_TYPES)}; got {ctype!r}",
                )
            elif ctype == "attack":
                n_attack += 1
            elif ctype == "benign":
                n_benign += 1
            elif ctype == "utility":
                n_utility += 1

        messages = obj.get("messages")
        if messages is None:
            add_issue("error", "missing_field", idx, case_id, "messages", "Missing required field: messages")
        elif not isinstance(messages, list) or len(messages) == 0:
            add_issue("error", "invalid_type", idx, case_id, "messages", "Field 'messages' must be a non-empty list")
        else:
            for midx, msg in enumerate(messages):
                field_prefix = f"messages[{midx}]"
                if not isinstance(msg, dict):
                    add_issue("error", "invalid_type", idx, case_id, field_prefix, "Message must be an object")
                    continue
                role = msg.get("role")
                content = msg.get("content")
                if not _nonempty_str(role):
                    add_issue("error", "invalid_type", idx, case_id, f"{field_prefix}.role", "role must be a non-empty string")
                elif role not in VALID_ROLES:
                    add_issue(
                        "error",
                        "invalid_value",
                        idx,
                        case_id,
                        f"{field_prefix}.role",
                        f"role must be one of {sorted(VALID_ROLES)}; got {role!r}",
                    )
                if not _nonempty_str(content):
                    add_issue(
                        "error",
                        "invalid_type",
                        idx,
                        case_id,
                        f"{field_prefix}.content",
                        "content must be a non-empty string",
                    )

        # Uniqueness
        if _nonempty_str(obj.get("id")):
            cid = obj["id"].strip()
            prev_idx = seen_ids.get(cid)
            if prev_idx is not None:
                add_issue(
                    "error",
                    "duplicate_id",
                    idx,
                    cid,
                    "id",
                    f"Duplicate id {cid!r}; first seen at index {prev_idx}",
                )
            else:
                seen_ids[cid] = idx

        # Soft requirements -> warnings
        if not _nonempty_str(obj.get("category")):
            add_issue("warning", "missing_category", idx, case_id, "category", "category is missing or empty")
        if not _nonempty_str(obj.get("family_id")):
            add_issue("warning", "missing_family_id", idx, case_id, "family_id", "family_id is missing or empty")

        # Utility checks
        if obj.get("type") == "utility":
            if obj.get("utility_task") is None:
                add_issue("error", "missing_field", idx, case_id, "utility_task", "Utility case must define utility_task")
            if _qa_like_utility_case(obj):
                ref = obj.get("reference")
                if not isinstance(ref, dict) or len(ref) == 0:
                    add_issue(
                        "error",
                        "missing_field",
                        idx,
                        case_id,
                        "reference",
                        "QA-like utility case must define non-empty reference",
                    )

    report = DatasetValidationReport(
        ok=(len(errors) == 0),
        dataset_path=str(path),
        generated_at=datetime.now(timezone.utc).isoformat(),
        counts={
            "n_items": len(items),
            "n_attack": n_attack,
            "n_benign": n_benign,
            "n_utility": n_utility,
            "n_errors": len(errors),
            "n_warnings": len(warnings),
        },
        errors=[asdict(x) for x in errors],
        warnings=[asdict(x) for x in warnings],
    )
    return report
