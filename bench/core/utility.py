from __future__ import annotations

import re
import string
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class UtilityScore:
    """Per-case utility score.

    `score` is a single scalar (for MCQ it's 0/1, for QA it's F1).
    `details` can include extra metrics (e.g., em, f1, accuracy).
    """

    task: str
    score: float
    details: Dict[str, float]


_MC_LETTERS = {"A", "B", "C", "D"}
_MC_CYR_TO_LAT = str.maketrans(
    {
        "А": "A",
        "В": "B",
        "С": "C",
        "Д": "D",
    }
)


def parse_mcq_letter(text: str) -> Optional[str]:
    """Extract A/B/C/D answer from model output with robust RU/EN patterns.

    Supported examples:
    - "Ответ: B"
    - "(B)"
    - "B."
    - "вариант B"
    - "я выбираю C"
    """
    if not text:
        return None

    txt = text.upper().translate(_MC_CYR_TO_LAT)

    # Strong cue phrases first (RU/EN).
    m = re.search(
        r"(?:\bОТВЕТ\b|\bANSWER\b|\bANS\b|\bВАРИАНТ\b|\bOPTION\b|\bЯ\s+ВЫБИРАЮ\b|\bВЫБИРАЮ\b|\bМОЙ\s+ОТВЕТ\b)\s*[:\-]?\s*[\(\[]?\s*([ABCD])\s*[\)\]]?",
        txt,
    )
    if m:
        return m.group(1)

    # Entire output is a single option token ("B", "(B)", "B.")
    m = re.search(r"^\s*[\(\[]?\s*([ABCD])\s*[\)\].,:;!\?]?\s*$", txt)
    if m:
        return m.group(1)

    # Parenthesized answer anywhere.
    m = re.search(r"\(([ABCD])\)", txt)
    if m:
        return m.group(1)

    # Standalone token with common punctuation.
    m = re.search(r"\b([ABCD])\s*[.)](?=\s|$)", txt)
    if m:
        return m.group(1)

    # Conservative fallback: only if exactly one isolated letter token exists.
    isolated = re.findall(r"\b([ABCD])\b", txt)
    if len(isolated) == 1:
        return isolated[0]

    return None


_PUNCT_TABLE = str.maketrans({c: " " for c in string.punctuation + "«»“”„”’‘—–…"})


def normalize_ru(text: str) -> str:
    """A lightweight normalizer for Russian extractive QA."""
    if text is None:
        return ""
    text = text.strip().lower()
    text = text.replace("ё", "е")
    text = text.translate(_PUNCT_TABLE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokenize(text: str) -> List[str]:
    text = normalize_ru(text)
    return [t for t in text.split() if t]


def f1_score(pred: str, gold: str) -> float:
    pred_toks = _tokenize(pred)
    gold_toks = _tokenize(gold)

    if not pred_toks and not gold_toks:
        return 1.0
    if not pred_toks or not gold_toks:
        return 0.0

    # multiset overlap
    from collections import Counter

    common = Counter(pred_toks) & Counter(gold_toks)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0

    precision = num_same / len(pred_toks)
    recall = num_same / len(gold_toks)
    return 2 * precision * recall / (precision + recall)


def exact_match(pred: str, gold: str) -> float:
    return 1.0 if normalize_ru(pred) == normalize_ru(gold) else 0.0


def squad_max_em_f1(pred: str, gold_answers: List[str]) -> Tuple[float, float]:
    """Return (EM, F1) against the best matching reference answer."""
    if not gold_answers:
        return 0.0, 0.0

    ems = [exact_match(pred, a) for a in gold_answers]
    f1s = [f1_score(pred, a) for a in gold_answers]
    return max(ems), max(f1s)


def score_rummlu(pred_text: str, gold_label: str) -> UtilityScore:
    pred = parse_mcq_letter(pred_text)
    if pred is None:
        raise ValueError("ruMMLU parse_error: could not parse option A/B/C/D from model output")
    gold = (gold_label or "").strip().upper()
    acc = 1.0 if pred is not None and pred == gold else 0.0
    return UtilityScore(task="rummlu_mcq", score=acc, details={"accuracy": acc, "predicted_option": pred})


def score_sberquad(pred_text: str, gold_answers: List[str]) -> UtilityScore:
    em, f1 = squad_max_em_f1(pred_text, gold_answers)
    return UtilityScore(task="sberquad_qa", score=f1, details={"em": em, "f1": f1})


def build_sberquad_debug(pred_text: str, gold_answers: List[str], *, max_chars: int = 160) -> Dict[str, Any]:
    """Compact normalized strings for per-case debugging in artifacts."""
    pred_norm = normalize_ru(pred_text or "")
    refs_norm = [normalize_ru(x or "") for x in (gold_answers or [])]

    def clip(s: str) -> str:
        if len(s) <= max_chars:
            return s
        return s[: max_chars - 3] + "..."

    return {
        "normalized_prediction": clip(pred_norm),
        "normalized_gold_answers": [clip(x) for x in refs_norm[:5]],
        "prediction_is_empty": (pred_norm == ""),
        "num_gold_answers": len(refs_norm),
    }
