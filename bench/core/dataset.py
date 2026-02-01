from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Dict, Any

import yaml

Role = Literal["system", "user", "assistant"]
ScenarioType = Literal["single_turn", "multi_turn"]
CaseType = Literal["attack", "benign"]

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
    expected_action: Literal["allow", "safe_refusal"]  # allow for benign, safe_refusal for attacks

    # Optional indicators to detect "attack success"
    goal_indicators: Optional[List[str]] = None

    meta: Dict[str, Any] = None

def _parse_case(obj: Dict[str, Any]) -> Case:
    msgs = [Message(role=m["role"], content=m["content"]) for m in obj["messages"]]
    return Case(
        case_id=str(obj["id"]),
        case_type=obj.get("type", "attack"),
        category=obj.get("category", "unknown"),
        family_id=obj.get("family_id", str(obj["id"])),
        scenario=obj.get("scenario", "single_turn"),
        messages=msgs,
        expected_action=obj.get("expected_action", "safe_refusal"),
        goal_indicators=obj.get("goal_indicators"),
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
    elif suffix == ".jsonl":
        cases: List[Case] = []
        with path.open("r", encoding="utf-8") as f:
            import json
            for line in f:
                line = line.strip()
                if not line:
                    continue
                cases.append(_parse_case(json.loads(line)))
        return cases
    else:
        raise ValueError(f"Unsupported dataset format: {path}")
