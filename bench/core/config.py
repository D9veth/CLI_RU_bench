from __future__ import annotations

from pathlib import Path
from typing import Optional, Literal, Dict, Any

import yaml
from pydantic import BaseModel, Field


ProviderName = Literal["openai_compatible"]

class TargetConfig(BaseModel):
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


class GenerationConfig(BaseModel):
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 512

class DefenseConfig(BaseModel):
    # MVP placeholders; replace with policy-as-code integration later.
    json_schema_path: Optional[str] = None

class RunSection(BaseModel):
    repeats: int = 1

class RunConfig(BaseModel):
    target: TargetConfig
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    defense: DefenseConfig = Field(default_factory=DefenseConfig)
    run: RunSection = Field(default_factory=RunSection)

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
        return RunConfig.model_validate(data)
