from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\ufeff\u2060]")
SPACING_RE = re.compile(r"\s+")
SEPARATOR_DEOBFUSCATION_RE = re.compile(r"(?<=\w)[\s._\-]+(?=\w)")
EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "]+"
)

HOMOGLYPHS = str.maketrans(
    {
        "а": "a",
        "е": "e",
        "о": "o",
        "р": "p",
        "с": "c",
        "у": "y",
        "х": "x",
        "к": "k",
        "м": "m",
        "т": "t",
        "в": "b",
        "н": "h",
        "і": "i",
        "ї": "i",
        "ё": "е",
        "А": "A",
        "Е": "E",
        "О": "O",
        "Р": "P",
        "С": "C",
        "У": "Y",
        "Х": "X",
        "К": "K",
        "М": "M",
        "Т": "T",
        "В": "B",
        "Н": "H",
        "І": "I",
        "Ї": "I",
        "Ё": "Е",
    }
)


@dataclass(frozen=True)
class NormalizedText:
    raw: str
    normalized: str
    changed: bool


def normalize_text(text: str, cfg=None) -> NormalizedText:
    if cfg is not None and not getattr(cfg, "enabled", True):
        return NormalizedText(raw=text or "", normalized=text or "", changed=False)

    current = text or ""
    current = unicodedata.normalize("NFKC", current)
    if _enabled(cfg, "strip_zero_width", True):
        current = ZERO_WIDTH_RE.sub("", current)
    if _enabled(cfg, "normalize_emoji", True):
        current = EMOJI_RE.sub(" [emoji] ", current)
    if _enabled(cfg, "normalize_homoglyphs", True):
        current = current.translate(HOMOGLYPHS)
    current = current.casefold()
    if _enabled(cfg, "deobfuscate_separators", True):
        current = _deobfuscate_known_phrases(current)
    if _enabled(cfg, "normalize_spacing", True):
        current = SPACING_RE.sub(" ", current).strip()
    return NormalizedText(raw=text or "", normalized=current, changed=current != (text or ""))


def _enabled(cfg, attr: str, default: bool) -> bool:
    if cfg is None:
        return default
    return bool(getattr(cfg, attr, default))


def _deobfuscate_known_phrases(text: str) -> str:
    compact = SEPARATOR_DEOBFUSCATION_RE.sub("", text)
    known = {
        "ignoreprevious": "ignore previous",
        "ignoreallprevious": "ignore all previous",
        "ignoresystem": "ignore system",
        "ignoreinstructions": "ignore instructions",
        "игнорируй": "игнорируй",
        "игнорируйпредыдущие": "игнорируй предыдущие",
        "раскройсистемныйпромпт": "раскрой системный промпт",
    }
    out = text
    for compact_phrase, replacement in known.items():
        if compact_phrase in compact:
            out = f"{out} {replacement}"
    return out
