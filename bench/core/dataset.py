from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml

Role = Literal["system", "user", "assistant"]
ScenarioType = Literal["single_turn", "multi_turn"]
CaseType = Literal["attack", "benign", "utility"]


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


def load_dataset(path: Path) -> List[Case]:
    """Load dataset from YAML (list) or JSONL."""
    suffix = path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("YAML dataset must be a list of cases.")
        return [_parse_case(x) for x in data]

    if suffix == ".jsonl":
        import json

        cases: List[Case] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                cases.append(_parse_case(json.loads(line)))
        return cases

    raise ValueError(f"Unsupported dataset format: {path}")
