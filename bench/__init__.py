from __future__ import annotations

__all__ = ["app"]


def __getattr__(name: str):
    if name == "app":
        from .cli import app

        return app
    raise AttributeError(name)

