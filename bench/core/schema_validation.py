from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from bench.core.paths import find_repo_root, resolve_config_path


@dataclass(frozen=True)
class SchemaValidationResult:
    enabled: bool
    schema_valid: bool | None
    status: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SchemaValidator:
    def __init__(self, schema_path: str | None, *, config_dir: Path | None = None):
        self.schema_path = schema_path
        self.config_dir = config_dir
        self._validator: Draft202012Validator | None = None
        if schema_path:
            path = resolve_config_path(
                schema_path,
                config_dir=config_dir,
                repo_root=find_repo_root(config_dir or Path.cwd()),
                label="json_schema_path",
            )
            schema = json.loads(path.read_text(encoding="utf-8"))
            self._validator = Draft202012Validator(schema)

    def validate_text(self, text: str) -> SchemaValidationResult:
        if self._validator is None:
            return SchemaValidationResult(enabled=False, schema_valid=None, status="schema_not_configured")
        try:
            payload = extract_json(text or "")
        except ValueError as exc:
            return SchemaValidationResult(
                enabled=True,
                schema_valid=False,
                status="schema_parse_error",
                error=str(exc),
            )
        try:
            self._validator.validate(payload)
        except ValidationError as exc:
            return SchemaValidationResult(
                enabled=True,
                schema_valid=False,
                status="schema_violation",
                error=exc.message,
            )
        return SchemaValidationResult(enabled=True, schema_valid=True, status="schema_valid")


def extract_json(text: str):
    stripped = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", stripped, flags=re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1).strip()
    candidates = [stripped]
    first_obj = stripped.find("{")
    last_obj = stripped.rfind("}")
    if first_obj >= 0 and last_obj > first_obj:
        candidates.append(stripped[first_obj : last_obj + 1])
    first_arr = stripped.find("[")
    last_arr = stripped.rfind("]")
    if first_arr >= 0 and last_arr > first_arr:
        candidates.append(stripped[first_arr : last_arr + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Model output does not contain valid JSON.")
