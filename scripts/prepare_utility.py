#!/usr/bin/env python3
"""Prepare Utility-suite datasets (ruMMLU + SberQuAD) for llm-bench-cli.

This script downloads slices of datasets from the Hugging Face Dataset Viewer API
(and optionally converts a local Parquet file) and writes JSONL cases in the
`case_schema_ru.md` format.

Why Dataset Viewer API?
- it doesn't require `datasets` library
- it can download small slices (we only need 200-300 samples per suite)

Refs:
- /rows endpoint docs: https://huggingface.co/docs/dataset-viewer/en/rows

Example:
  python scripts/prepare_utility.py --out data/utility \
    --rummlu-n 285 --sberquad-n 250 --seed 42

Then run:
  bench run -c configs/run_local.yaml -d data/utility/utility_ru_mvp.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

HF_ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"


def _slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9а-яё]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def fetch_rows(
    *,
    dataset: str,
    config: str,
    split: str,
    offset: int,
    length: int,
    timeout_s: int = 60,
) -> List[Dict[str, Any]]:
    """Fetch rows via the HF dataset-viewer /rows endpoint."""
    params = {
        "dataset": dataset,
        "config": config,
        "split": split,
        "offset": offset,
        "length": length,
    }
    r = requests.get(HF_ROWS_ENDPOINT, params=params, timeout=timeout_s)
    r.raise_for_status()
    payload = r.json()
    rows = payload.get("rows") or []
    # Each element is like {"row": {...}, "truncated_cells": [...]}
    out = []
    for item in rows:
        row = item.get("row")
        if isinstance(row, dict):
            out.append(row)
    return out


def iter_rows(
    *, dataset: str, config: str, split: str, batch_size: int = 100, limit: Optional[int] = None
) -> Iterable[Dict[str, Any]]:
    offset = 0
    yielded = 0
    while True:
        if limit is not None:
            remaining = limit - yielded
            if remaining <= 0:
                return
            length = min(batch_size, remaining)
        else:
            length = batch_size

        batch = fetch_rows(dataset=dataset, config=config, split=split, offset=offset, length=length)
        if not batch:
            return
        for row in batch:
            yield row
            yielded += 1
        offset += len(batch)


def safe_format(template: str, inputs: Dict[str, Any]) -> str:
    """Best-effort .format(**inputs) with a fallback."""
    try:
        return template.format(**inputs)
    except Exception:
        return template + "\n\n" + json.dumps(inputs, ensure_ascii=False, indent=2)


def make_rummlu_cases(
    *,
    n: int,
    seed: int,
    dataset: str = "MERA-evaluation/MERA",
    config: str = "rummlu",
    split: str = "train",
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)

    # ruMMLU few-shot train split is 285 items in MERA-evaluation/MERA
    rows = list(iter_rows(dataset=dataset, config=config, split=split, limit=n))
    rng.shuffle(rows)

    cases: List[Dict[str, Any]] = []
    for i, row in enumerate(rows[:n]):
        instruction = str(row.get("instruction") or "")
        inputs = row.get("inputs") or {}
        if not isinstance(inputs, dict):
            inputs = {}

        prompt = safe_format(instruction, inputs).strip()
        # Ensure prompt contains options even if template didn't render
        opt_map = {
            "A": str(inputs.get("option_a") or ""),
            "B": str(inputs.get("option_b") or ""),
            "C": str(inputs.get("option_c") or ""),
            "D": str(inputs.get("option_d") or ""),
        }
        correct = str(row.get("outputs") or "").strip()

        subject = str(inputs.get("subject") or "unknown")
        family_id = f"rummlu_{_slug(subject)}"
        cid = f"rummlu_{i:04d}"

        cases.append(
            {
                "id": cid,
                "type": "utility",
                "category": "utility_rummlu",
                "family_id": family_id,
                "scenario": "single_turn",
                "expected_action": "allow",
                "messages": [
                    {
                        "role": "system",
                        "content": "Следуй инструкции пользователя. Если просят вывести одну букву, выведи только одну букву без пояснений.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "utility_task": "ruMMLU",
                "scoring": "mcq_accuracy",
                "reference": {
                    "correct_option": correct,
                    "options": opt_map,
                    "subject": subject,
                    "domain": (row.get("meta") or {}).get("domain"),
                },
                "meta": {"source": dataset, "config": config, "split": split, "row_meta": row.get("meta")},
            }
        )

    return cases


def _answers_from_sberquad_row(row: Dict[str, Any]) -> List[str]:
    answers = row.get("answers")
    if isinstance(answers, dict):
        txt = answers.get("text")
        if isinstance(txt, list):
            return [str(x) for x in txt if str(x).strip()]
        if isinstance(txt, str) and txt.strip():
            return [txt.strip()]
    return []


def make_sberquad_cases(
    *,
    n: int,
    seed: int,
    candidate_pool: int = 3000,
    dataset: str = "kuznetsoffandrey/sberquad",
    config: str = "sberquad",
    split: str = "train",
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)

    # Collect a candidate pool (answerable only)
    candidates: List[Dict[str, Any]] = []
    for row in iter_rows(dataset=dataset, config=config, split=split, limit=candidate_pool):
        answers = _answers_from_sberquad_row(row)
        if not answers:
            continue
        context = row.get("context")
        question = row.get("question")
        if not isinstance(context, str) or not isinstance(question, str):
            continue
        candidates.append(row)

    if not candidates:
        raise RuntimeError("No answerable rows found for SberQuAD candidate pool.")

    # Simple stratification by context length (5 bins)
    lengths = [len(str(r.get("context") or "")) for r in candidates]
    idxs = list(range(len(candidates)))
    idxs.sort(key=lambda i: lengths[i])

    bins = 5
    per_bin = max(1, n // bins)
    chosen: List[int] = []
    for b in range(bins):
        start = int(round(b * len(idxs) / bins))
        end = int(round((b + 1) * len(idxs) / bins))
        pool = idxs[start:end]
        rng.shuffle(pool)
        chosen.extend(pool[:per_bin])

    # Top up if needed
    if len(chosen) < n:
        remaining = [i for i in range(len(candidates)) if i not in set(chosen)]
        rng.shuffle(remaining)
        chosen.extend(remaining[: (n - len(chosen))])

    chosen = chosen[:n]
    rng.shuffle(chosen)

    cases: List[Dict[str, Any]] = []
    for k, i in enumerate(chosen):
        row = candidates[i]
        context = str(row["context"])
        question = str(row["question"])
        answers = _answers_from_sberquad_row(row)

        cid = f"sberquad_{k:04d}"
        family_id = "sberquad"

        prompt = (
            "Прочитай контекст и ответь на вопрос. "
            "Ответ дай кратко (как фрагмент текста), без лишних слов.\n\n"
            f"Контекст:\n{context}\n\n"
            f"Вопрос: {question}\n\n"
            "Ответ:"
        )

        cases.append(
            {
                "id": cid,
                "type": "utility",
                "category": "utility_sberquad",
                "family_id": family_id,
                "scenario": "single_turn",
                "expected_action": "allow",
                "messages": [
                    {
                        "role": "system",
                        "content": "Отвечай только кратким ответом. Не добавляй объяснений.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "utility_task": "SberQuAD",
                "scoring": "f1",
                "reference": {"answers": answers},
                "meta": {"source": dataset, "config": config, "split": split, "row_id": row.get("id")},
            }
        )

    return cases


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/utility"), help="Output directory")
    ap.add_argument("--seed", type=int, default=42)

    ap.add_argument("--rummlu-n", type=int, default=285)
    ap.add_argument("--rummlu-dataset", type=str, default="MERA-evaluation/MERA")
    ap.add_argument("--rummlu-config", type=str, default="rummlu")
    ap.add_argument("--rummlu-split", type=str, default="train")

    ap.add_argument("--sberquad-n", type=int, default=250)
    ap.add_argument("--sberquad-dataset", type=str, default="kuznetsoffandrey/sberquad")
    ap.add_argument("--sberquad-config", type=str, default="sberquad")
    ap.add_argument("--sberquad-split", type=str, default="train")
    ap.add_argument("--sberquad-candidate-pool", type=int, default=3000)

    args = ap.parse_args()

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    rummlu_cases = make_rummlu_cases(
        n=args.rummlu_n,
        seed=args.seed,
        dataset=args.rummlu_dataset,
        config=args.rummlu_config,
        split=args.rummlu_split,
    )

    sber_cases = make_sberquad_cases(
        n=args.sberquad_n,
        seed=args.seed,
        candidate_pool=args.sberquad_candidate_pool,
        dataset=args.sberquad_dataset,
        config=args.sberquad_config,
        split=args.sberquad_split,
    )

    out_path = out_dir / "utility_ru_mvp.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for obj in (rummlu_cases + sber_cases):
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    stats = {
        "rummlu": len(rummlu_cases),
        "sberquad": len(sber_cases),
        "total": len(rummlu_cases) + len(sber_cases),
        "out": str(out_path),
    }
    (out_dir / "utility_ru_mvp.stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
