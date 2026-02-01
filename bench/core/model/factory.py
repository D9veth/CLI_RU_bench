from __future__ import annotations

from bench.core.config import TargetConfig
from bench.core.model.openai_compatible import OpenAICompatibleClient

def build_client(target: TargetConfig):
    if target.provider == "openai_compatible":
        return OpenAICompatibleClient(target)
    raise ValueError(f"Unsupported provider: {target.provider}")
