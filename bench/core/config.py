from __future__ import annotations

from pathlib import Path
from typing import Optional, Literal, Dict, Any, List

import yaml
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr, field_validator, model_validator


ProviderName = Literal["openai_compatible"]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TargetConfig(StrictBaseModel):
    provider: ProviderName = "openai_compatible"

    endpoint_url: Optional[str] = Field(
        None, description="Full URL to chat-completions endpoint, e.g. http://host:8000/v1/chat/completions"
    )

    base_url: Optional[str] = Field(
        None, description="Base URL, e.g. http://host:8000/v1 or http://host:8000"
    )
    chat_path: str = Field(
        "/chat/completions", description="Path appended to base_url if endpoint_url is not set."
    )

    model: str = Field(..., description="Model name or deployment id.")
    api_key_env: Optional[str] = Field("OPENAI_API_KEY", description="Env var holding API key/token.")
    auth_header: str = Field("Authorization", description="Header name for auth.")
    auth_scheme: str = Field("Bearer", description="Auth scheme prefix, e.g. Bearer. Can be empty.")
    timeout_sec: int = 60
    retries: int = 2
    max_concurrency: int = 1

    headers: Dict[str, str] = Field(default_factory=dict)

    def resolved_endpoint(self) -> str:
        if self.endpoint_url:
            return self.endpoint_url.rstrip("/")
        if not self.base_url:
            raise ValueError("Either target.endpoint_url or target.base_url must be set.")
        base = self.base_url.rstrip("/")
        path = self.chat_path
        if not path.startswith("/"):
            path = "/" + path
        return base + path


class GenerationConfig(StrictBaseModel):
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 512


class FilterConfig(StrictBaseModel):
    enabled: bool = True
    patterns: List[str] = Field(default_factory=list)
    mode: str = "regex"
    action: str = "block"
    case_sensitive: bool = False


class NormalizationConfig(StrictBaseModel):
    enabled: bool = True
    strip_zero_width: bool = True
    normalize_homoglyphs: bool = True
    normalize_spacing: bool = True
    deobfuscate_separators: bool = True
    normalize_emoji: bool = True


class DLPStageConfig(StrictBaseModel):
    action: str = "audit"
    severity_threshold: str = "low"


class DLPConfig(StrictBaseModel):
    enabled: bool = False
    input: DLPStageConfig = Field(default_factory=lambda: DLPStageConfig(action="audit"))
    output: DLPStageConfig = Field(default_factory=lambda: DLPStageConfig(action="redact"))
    store_raw_findings: bool = False


class SchemaValidationConfig(StrictBaseModel):
    enabled: bool = False
    stage: str = "output"
    action: str = "mark_error"
    retry_on_violation: bool = False
    max_retries: int = 0


class PolicyConfig(StrictBaseModel):
    enabled: bool = False
    rules_paths: List[str] = Field(default_factory=lambda: ["policies/rules/ru_guardrails.yaml"])
    engine: str = "local"
    opa_url: Optional[str] = None


class DuringGuardConfig(StrictBaseModel):
    enabled: bool = False
    mode: str = "streaming"
    action: str = "stop_and_refuse"


class DefenseConfig(StrictBaseModel):
    profile: str = "D0"
    system_prompt_path: Optional[str] = None
    system_prompt_text: Optional[str] = None

    wrap_user_messages: bool = False
    wrap_template_path: Optional[str] = None
    wrap_template_text: Optional[str] = None
    user_wrap_prefix: Optional[str] = None
    user_wrap_suffix: Optional[str] = None

    prefilter: Optional[FilterConfig] = None
    postfilter: Optional[FilterConfig] = None
    # Legacy flat fields still used in existing configs/defenses/*.yaml
    prefilter_patterns: Optional[List[str]] = None
    postfilter_patterns: Optional[List[str]] = None

    refusal_template_path: Optional[str] = None
    refusal_template_text: Optional[str] = None
    json_schema_path: Optional[str] = None
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)
    dlp: DLPConfig = Field(default_factory=DLPConfig)
    schema_validation: SchemaValidationConfig = Field(default_factory=SchemaValidationConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    during_guard: DuringGuardConfig = Field(default_factory=DuringGuardConfig)
    tags: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

    @field_validator("profile")
    @classmethod
    def _normalize_profile(cls, value: str) -> str:
        value = (value or "D0").strip().upper()
        if not value:
            return "D0"
        return value

    @model_validator(mode="after")
    def _normalize_legacy_filter_fields(self) -> "DefenseConfig":
        if self.prefilter is None and self.prefilter_patterns is not None:
            self.prefilter = FilterConfig(
                enabled=True,
                patterns=list(self.prefilter_patterns),
                action="block",
            )
        if self.postfilter is None and self.postfilter_patterns is not None:
            self.postfilter = FilterConfig(
                enabled=True,
                patterns=list(self.postfilter_patterns),
                action="block",
            )
        return self


class RunSection(StrictBaseModel):
    repeats: int = 1
    use_cache: bool = False
    cache_dir: Optional[str] = None
    execution_mode: str = "sequential"


class RunConfig(StrictBaseModel):
    target: TargetConfig
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    defense: DefenseConfig = Field(default_factory=DefenseConfig)
    run: RunSection = Field(default_factory=RunSection)
    _source_path: Optional[Path] = PrivateAttr(default=None)

    @property
    def source_path(self) -> Optional[Path]:
        return self._source_path

    @property
    def source_dir(self) -> Path:
        if self._source_path is not None:
            return self._source_path.parent
        return Path.cwd()

    @staticmethod
    def load(path: Path) -> "RunConfig":
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(raw)
        elif path.suffix.lower() == ".json":
            import json
            data = json.loads(raw)
        else:
            raise ValueError(f"Unsupported config format: {path}")
        cfg = RunConfig.model_validate(data)
        cfg._source_path = path.resolve()
        return cfg
