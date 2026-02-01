from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Any

from bench.core.config import RunConfig
from bench.core.dataset import Case
from bench.core.evaluator import evaluate_case_mvp, looks_like_refusal
from bench.core.metrics import aggregate_metrics
from bench.core.storage import write_cases_jsonl
from bench.core.utility import score_rummlu, score_sberquad


def _get_utility_task_name(case: Case) -> str:
    if not case.utility_task:
        return "unknown"
    if isinstance(case.utility_task, dict):
        return (
            case.utility_task.get("name")
            or case.utility_task.get("task")
            or case.utility_task.get("suite")
            or "unknown"
        )
    return str(case.utility_task)


def _score_utility(case: Case, response_text: str):
    """Return (utility_task_name, utility_score, utility_details)."""
    tname = _get_utility_task_name(case)
    low = tname.lower()
    ref = case.reference or {}

    if "mmlu" in low:
        gold = (ref.get("correct_option") or ref.get("label") or ref.get("gold") or "").strip()
        us = score_rummlu(response_text, gold)
        return tname, us.score, us.details

    if "squad" in low or "sber" in low:
        answers = ref.get("answers") or ref.get("gold_answers") or []
        if isinstance(answers, str):
            answers = [answers]
        us = score_sberquad(response_text, list(answers))
        return tname, us.score, us.details

    return tname, None, None

def _messages_to_dicts(case: Case) -> List[Dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in case.messages]

def _extract_text(openai_like: Dict[str, Any]) -> str:
    try:
        return openai_like["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""

def run_benchmark(client, run_cfg: RunConfig, cases: List[Case], run_dir: Path):
    rows: List[Dict[str, Any]] = []
    cases_by_id = {c.case_id: c for c in cases}

    for case in cases:
        for rep in range(run_cfg.run.repeats):
            t0 = time.perf_counter()
            raw = client.generate(
                messages=_messages_to_dicts(case),
                model=run_cfg.target.model,
                temperature=run_cfg.generation.temperature,
                top_p=run_cfg.generation.top_p,
                max_tokens=run_cfg.generation.max_tokens,
            )
            latency_ms = float(raw.get("_latency_ms") or (time.perf_counter() - t0) * 1000.0)
            text = _extract_text(raw)

            row = {
                "case_id": case.case_id,
                "repeat": rep,
                "category": case.category,
                "family_id": case.family_id,
                "case_type": case.case_type,
                "expected_action": case.expected_action,
                "latency_ms": latency_ms,
                "response_text": text,
            }

            # Safety-suite scoring
            if case.case_type in {"attack", "benign"}:
                ev = evaluate_case_mvp(
                    response_text=text,
                    expected_action=case.expected_action,
                    goal_indicators=case.goal_indicators,
                )
                row.update(
                    {
                        "refused": ev["refused"],
                        "success": ev["success"],
                        "goal_hit": ev.get("goal_hit", False),
                    }
                )
            else:
                # Utility-suite scoring
                row["refused"] = looks_like_refusal(text)
                row["success"] = None
                row["goal_hit"] = False

                tname, uscore, udetails = _score_utility(case, text)
                row["utility_task"] = tname
                row["utility_score"] = uscore
                row["utility_details"] = udetails

            rows.append(row)

    write_cases_jsonl(run_dir, rows)
    summary = aggregate_metrics(rows, cases_by_id)
    return rows, summary
