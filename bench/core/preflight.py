from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from bench.core.config import RunConfig

class PreflightResult(BaseModel):
    ok: bool
    provider: str
    base_url: str
    model: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    raw_sample: Optional[Dict[str, Any]] = None

def run_preflight(client, run_cfg: RunConfig) -> PreflightResult:
    try:
        data = client.generate(
            messages=[{"role": "user", "content": "ping"}],
            model=run_cfg.target.model,
            temperature=0.0,
            top_p=1.0,
            max_tokens=8,
        )
        latency = float(data.get("_latency_ms")) if data.get("_latency_ms") is not None else None
        # Extract a small snippet
        content = None
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            pass
        ok = content is not None
        return PreflightResult(
            ok=ok,
            provider=run_cfg.target.provider,
            base_url=run_cfg.target.base_url,
            model=run_cfg.target.model,
            latency_ms=latency,
            raw_sample={"content": content, "usage": data.get("usage")},
        )
    except Exception as e:
        return PreflightResult(
            ok=False,
            provider=run_cfg.target.provider,
            base_url=run_cfg.target.base_url,
            model=run_cfg.target.model,
            error=str(e),
        )
