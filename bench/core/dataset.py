from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml

Role = Literal["system", "user", "assistant"]
ScenarioType = Literal["single_turn", "multi_turn"]
CaseType = Literal["attack", "benign", "utility"]
VALID_ROLES = {"system", "user", "assistant"}
VALID_CASE_TYPES = {"attack", "benign", "utility"}


@dataclass
class Message:
    role: Role
    content: str


@dataclass
class Case:
    case_id: str
    case_type: CaseType
    category: str
    family_id: str
    scenario: ScenarioType
    messages: List[Message]

    # Expectations (MVP)
    expected_action: Literal["allow", "safe_refusal"]

    # Optional indicators to detect "attack success"
    goal_indicators: Optional[List[str]] = None

    # Utility-only fields (optional; only present when case_type == "utility")
    utility_task: Optional[Dict[str, Any]] = None
    reference: Optional[Dict[str, Any]] = None

    meta: Dict[str, Any] = None


def _default_expected_action(case_type: str) -> str:
    return "safe_refusal" if case_type == "attack" else "allow"


def _parse_case(obj: Dict[str, Any]) -> Case:
    msgs = [Message(role=m["role"], content=m["content"]) for m in obj["messages"]]
    ctype = obj.get("type", "attack")

    # Utility suite compatibility:
    # - spec allows `utility_task` as a string ("ruMMLU", "SberQuAD")
    # - implementation stores it as a dict for extensibility
    utility_task = obj.get("utility_task")
    if isinstance(utility_task, str):
        utility_task = {"name": utility_task}
    elif isinstance(utility_task, dict):
        utility_task = utility_task
    else:
        utility_task = None

    reference = obj.get("reference")
    if isinstance(reference, dict):
        reference = reference
    else:
        reference = None

    return Case(
        case_id=str(obj["id"]),
        case_type=ctype,
        category=obj.get("category", "unknown"),
        family_id=obj.get("family_id", str(obj["id"])),
        scenario=obj.get("scenario", "single_turn"),
        messages=msgs,
        expected_action=obj.get("expected_action") or _default_expected_action(ctype),
        goal_indicators=obj.get("goal_indicators"),
        utility_task=utility_task,
        reference=reference,
        meta=obj.get("meta", {}) or {},
    )


def load_dataset_objects(path: Path) -> List[Dict[str, Any]]:
    """Load raw dataset objects from YAML (list) or JSONL without coercing into Case."""
    suffix = path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("YAML dataset must be a list of cases.")
        if not all(isinstance(x, dict) for x in data):
            raise ValueError("Each YAML dataset item must be an object.")
        return list(data)

    if suffix == ".jsonl":
        import json

        items: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError(f"JSONL line {line_no}: each record must be an object.")
                items.append(obj)
        return items

    raise ValueError(f"Unsupported dataset format: {path}")


def load_dataset(path: Path) -> List[Case]:
    """Load dataset from YAML (list) or JSONL."""
    return [_parse_case(x) for x in load_dataset_objects(path)]
