#!/usr/bin/env python3
"""Convert local SberQuAD Parquet files into llm-bench-cli Utility cases (JSONL).

Usage:
  python scripts/convert_sberquad_parquet.py \
    --parquet train-00000-of-00001.parquet \
    --out data/utility/sberquad_from_parquet.jsonl \
    --n 250 --seed 42

Notes:
- Requires `pandas` and a Parquet engine (`pyarrow` recommended).
- Filters to answerable questions (answers.text not empty).
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List


def _answers(row: Dict[str, Any]) -> List[str]:
    ans = row.get("answers")
    if isinstance(ans, dict):
        txt = ans.get("text")
        if isinstance(txt, list):
            return [str(x) for x in txt if str(x).strip()]
        if isinstance(txt, str) and txt.strip():
            return [txt.strip()]
    return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=250)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise SystemExit(f"pandas is required: {e}")

    try:
        df = pd.read_parquet(args.parquet)
    except Exception as e:
        raise SystemExit(
            "Failed to read Parquet. Install a parquet engine, e.g.: pip install pyarrow\n"
            f"Error: {e}"
        )

    records = df.to_dict(orient="records")
    records = [r for r in records if _answers(r) and isinstance(r.get("context"), str) and isinstance(r.get("question"), str)]

    rng = random.Random(args.seed)
    rng.shuffle(records)
    records = records[: args.n]

    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        for i, r in enumerate(records):
            prompt = (
                "Прочитай контекст и ответь на вопрос. Ответ дай кратко, без лишних слов.\n\n"
                f"Контекст:\n{r['context']}\n\n"
                f"Вопрос: {r['question']}\n\n"
                "Ответ:"
            )
            obj = {
                "id": f"sberquad_parquet_{i:04d}",
                "type": "utility",
                "category": "utility_sberquad",
                "family_id": "sberquad",
                "scenario": "single_turn",
                "expected_action": "allow",
                "messages": [
                    {"role": "system", "content": "Отвечай только кратким ответом. Не добавляй объяснений."},
                    {"role": "user", "content": prompt},
                ],
                "utility_task": "SberQuAD",
                "reference": {"answers": _answers(r)},
                "meta": {"source": str(args.parquet), "row_id": r.get("id")},
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(json.dumps({"out": str(out), "n": len(records)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
