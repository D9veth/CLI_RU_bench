from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Any

from bench.core.config import RunConfig
from bench.core.dataset import Case
from bench.core.evaluator import evaluate_case_mvp
from bench.core.metrics import aggregate_metrics
from bench.core.storage import write_cases_jsonl

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

            ev = evaluate_case_mvp(
                response_text=text,
                expected_action=case.expected_action,
                goal_indicators=case.goal_indicators,
            )

            rows.append({
                "case_id": case.case_id,
                "repeat": rep,
                "category": case.category,
                "family_id": case.family_id,
                "case_type": case.case_type,
                "expected_action": case.expected_action,
                "refused": ev["refused"],
                "success": ev["success"],
                "goal_hit": ev.get("goal_hit", False),
                "latency_ms": latency_ms,
                "response_text": text,
            })

    write_cases_jsonl(run_dir, rows)
    summary = aggregate_metrics(rows, cases_by_id)
    return rows, summary
