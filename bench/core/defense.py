from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional

from bench.core.config import FilterConfig, RunConfig
from bench.core.dataset import Case


_PROFILE_LEVELS = {
    "D0": 0,
    "D1": 1,
    "D2": 2,
    "D3": 3,
}

_DEFAULT_REFUSAL = "I cannot help with that request."


@dataclass
class FilterResult:
    hit: bool
    stage: str
    matched_pattern: Optional[str] = None
    action_taken: Optional[str] = None


@dataclass
class _CompiledFilter:
    cfg: FilterConfig
    rules: List[tuple[str, re.Pattern]]
    stage: str


class DefensePipeline:
    def __init__(self, run_cfg: RunConfig):
        self.run_cfg = run_cfg
        self.cfg = run_cfg.defense
        self.profile = (self.cfg.profile or "D0").upper()
        self.profile_level = _PROFILE_LEVELS.get(self.profile, 0)
        self.base_dir = run_cfg.source_dir

        self._system_prompt_text = self._load_text(self.cfg.system_prompt_path, self.cfg.system_prompt_text)
        self._refusal_template_text = self._load_text(
            self.cfg.refusal_template_path, self.cfg.refusal_template_text
        ) or _DEFAULT_REFUSAL
        self._wrap_template_text = self._load_text(self.cfg.wrap_template_path, self.cfg.wrap_template_text)
        self._prefilter = self._compile_filter(self.cfg.prefilter, stage="prefilter")
        self._postfilter = self._compile_filter(self.cfg.postfilter, stage="postfilter")

    def effective_stages(self) -> List[str]:
        stages: List[str] = [self.profile]
        if self.system_prompt_enabled:
            stages.append("system")
        if self.wrap_enabled:
            stages.append("wrap")
        if self.prefilter_enabled:
            stages.append("prefilter")
        if self.postfilter_enabled:
            stages.append("postfilter")
        return stages

    def effective_label(self) -> str:
        stages = [s for s in self.effective_stages() if s not in {"D0", "D1", "D2", "D3"}]
        if not stages:
            return self.profile
        return f"{self.profile}[{'+'.join(stages)}]"

    @property
    def system_prompt_enabled(self) -> bool:
        return self.profile_level >= 1 and bool(self._system_prompt_text)

    @property
    def wrap_enabled(self) -> bool:
        return self.profile_level >= 2 and bool(self.cfg.wrap_user_messages)

    @property
    def prefilter_enabled(self) -> bool:
        return self.profile_level >= 2 and self._prefilter is not None

    @property
    def postfilter_enabled(self) -> bool:
        return self.profile_level >= 3 and self._postfilter is not None

    @property
    def refusal_template(self) -> str:
        return self._refusal_template_text

    def prepare_messages(self, case: Case) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        if self.system_prompt_enabled:
            out.append({"role": "system", "content": self._system_prompt_text or ""})

        for m in case.messages:
            content = m.content
            if m.role == "user" and self.wrap_enabled:
                content = self._wrap_user_content(content)
            out.append({"role": m.role, "content": content})
        return out

    def prefilter(self, case: Case, messages: List[Dict[str, str]]) -> FilterResult:
        del case  # reserved for future per-case rules
        if not self.prefilter_enabled or self._prefilter is None:
            return FilterResult(hit=False, stage="prefilter")
        # Inspect only user messages to avoid false hits on system hardening text itself.
        text = "\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
        return self._run_filter(self._prefilter, text)

    def postfilter(self, case: Case, model_text: str) -> FilterResult:
        del case  # reserved for future per-case rules
        if not self.postfilter_enabled or self._postfilter is None:
            return FilterResult(hit=False, stage="postfilter")
        return self._run_filter(self._postfilter, model_text or "")

    def _wrap_user_content(self, content: str) -> str:
        if self._wrap_template_text:
            tpl = self._wrap_template_text
            if "{{content}}" in tpl:
                return tpl.replace("{{content}}", content)
            if "{content}" in tpl:
                try:
                    return tpl.format(content=content)
                except Exception:
                    pass
            return tpl + content
        prefix = self.cfg.user_wrap_prefix or ""
        suffix = self.cfg.user_wrap_suffix or ""
        return f"{prefix}{content}{suffix}"

    def _load_text(self, path_value: Optional[str], inline_value: Optional[str]) -> Optional[str]:
        if inline_value:
            return inline_value
        if not path_value:
            return None
        p = Path(path_value)
        if not p.is_absolute():
            p = self.base_dir / p
        return p.read_text(encoding="utf-8")

    def _compile_filter(self, cfg: Optional[FilterConfig], stage: str) -> Optional[_CompiledFilter]:
        if cfg is None or not cfg.enabled or not cfg.patterns:
            return None
        if cfg.mode != "regex":
            raise ValueError(f"Unsupported filter mode for {stage}: {cfg.mode!r}")
        flags = 0 if cfg.case_sensitive else re.IGNORECASE
        rules: List[tuple[str, re.Pattern]] = []
        for pattern in cfg.patterns:
            rules.append((pattern, re.compile(pattern, flags=flags)))
        return _CompiledFilter(cfg=cfg, rules=rules, stage=stage)

    def _run_filter(self, flt: _CompiledFilter, text: str) -> FilterResult:
        for pattern, compiled in flt.rules:
            if compiled.search(text or ""):
                action = self._action_taken_for_stage(flt.stage, flt.cfg.action)
                return FilterResult(
                    hit=True,
                    stage=flt.stage,
                    matched_pattern=pattern,
                    action_taken=action,
                )
        return FilterResult(hit=False, stage=flt.stage)

    def _action_taken_for_stage(self, stage: str, action: str) -> str:
        action_norm = (action or "block").strip().lower()
        if stage == "prefilter":
            if action_norm == "allow":
                return "allowed"
            return "blocked"
        if action_norm == "redact":
            return "redacted"
        return "forced_refusal"

