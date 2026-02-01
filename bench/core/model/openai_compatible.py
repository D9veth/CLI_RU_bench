from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

from bench.core.config import TargetConfig


class OpenAICompatibleClient:
    """Client for OpenAI-compatible Chat Completions endpoint: POST /chat/completions."""

    def __init__(self, cfg: TargetConfig):
        self.cfg = cfg
        if getattr(cfg, "endpoint_url", None):
            self.endpoint_url = cfg.endpoint_url.rstrip("/")
        else:
            # иначе собираем из base_url + /chat/completions
            base = cfg.base_url.rstrip("/")
            self.endpoint_url = base + "/chat/completions"
        self.session = requests.Session()

        api_key = os.environ.get(cfg.api_key_env, "")
        if not api_key:
            raise RuntimeError(
                f"Missing API key in env var '{cfg.api_key_env}'. "
                f"Export it or set target.api_key_env in config."
            )
        self.api_key = api_key

    def chat_completions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self.endpoint_url
        headers = {"Content-Type": "application/json"}
        headers.update(self.cfg.headers or {})

        if self.cfg.api_key_env:
            api_key = os.environ.get(self.cfg.api_key_env, "")
            if not api_key:
                raise RuntimeError(f"Missing API key in env var '{self.cfg.api_key_env}'.")
            if self.cfg.auth_scheme:
                headers[self.cfg.auth_header] = f"{self.cfg.auth_scheme} {api_key}"
            else:
                headers[self.cfg.auth_header] = api_key

        last_err: Optional[Exception] = None
        for attempt in range(self.cfg.retries + 1):
            try:
                t0 = time.perf_counter()
                r = self.session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.cfg.timeout_sec,
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0

                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")

                try:
                    data = r.json()
                except Exception:
                    raise RuntimeError(f"Non-JSON response: {r.text[:500]}")

                if not isinstance(data, dict):
                    raise RuntimeError(f"Non-object JSON response: {data!r}; raw={r.text[:500]}")

                data["_latency_ms"] = latency_ms
                return data

            except Exception as e:
                last_err = e
                if attempt >= self.cfg.retries:
                    break

        raise RuntimeError(f"Chat completion failed after retries: {last_err}")

    def generate(self, messages: List[Dict[str, str]], *, model: str, temperature: float, top_p: float, max_tokens: int) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }
        return self.chat_completions(payload)
