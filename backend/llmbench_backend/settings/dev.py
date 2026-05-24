from .base import *  # noqa: F401,F403


SECRET_KEY = "django-insecure-llm-bench-backend-dev-only"
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "llmtest.local"]

DATABASES = {
    "default": database_from_url(None),
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://llmtest.local:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://llmtest.local:5174",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://llmtest.local:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://llmtest.local:5174",
    "http://llmtest.local:8000",
]
