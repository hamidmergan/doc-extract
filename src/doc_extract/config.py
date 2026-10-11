"""Default values and resolution of settings.

Order: argument, then environment variable, then default.
"""

import os
from dataclasses import dataclass
from typing import Optional

from .errors import ConfigError

# Limits
MAX_FILE_MB = 20
MAX_PAGES = 50
MAX_FILES = 20
MAX_IMAGE_SIDE = 2000

# Verarbeitung
PDF_RENDER_SCALE = 2.0
CONCURRENCY = 4
TIMEOUT_SECONDS = 120
MAX_RETRIES = 2

# Placeholder, because the OpenAI library requires a value.
# Lokale Server ignorieren ihn.
PLACEHOLDER_API_KEY = "not-needed"

ENV_PREFIX = "DOC_EXTRACT_"

DEFAULT_PROMPT = (
    "Transcribe all text visible in this image into Markdown. "
    "Keep the reading order. Use Markdown headings for headings, lists for lists "
    "and Markdown tables for tables. Do not translate, summarize or explain. "
    "Do not add any comment of your own. "
    "If the image contains no text, answer with an empty message."
)


@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    api_key: str
    max_file_mb: float
    max_pages: int
    max_files: int
    max_image_side: int
    pdf_render_scale: float
    concurrency: int
    timeout: float
    max_retries: int
    prompt: str


def _env(name: str) -> Optional[str]:
    value = os.environ.get(ENV_PREFIX + name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _pick(arg, env_name: str, default, cast):
    if arg is not None:
        return arg
    raw = _env(env_name)
    if raw is None:
        return default
    try:
        return cast(raw)
    except ValueError:
        raise ConfigError(
            f"Environment variable {ENV_PREFIX}{env_name} has an invalid value: {raw!r}"
        )


def resolve(
    *,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_file_mb: Optional[float] = None,
    max_pages: Optional[int] = None,
    max_files: Optional[int] = None,
    max_image_side: Optional[int] = None,
    pdf_render_scale: Optional[float] = None,
    concurrency: Optional[int] = None,
    timeout: Optional[float] = None,
    max_retries: Optional[int] = None,
    prompt: Optional[str] = None,
) -> Settings:
    base_url = _pick(base_url, "BASE_URL", None, str)
    model = _pick(model, "MODEL", None, str)
    missing = []
    if not base_url:
        missing.append("base_url (--base-url or DOC_EXTRACT_BASE_URL)")
    if not model:
        missing.append("model (--model or DOC_EXTRACT_MODEL)")
    if missing:
        raise ConfigError(
            "Missing: " + " and ".join(missing) + ". "
            "Example for Ollama: base_url http://localhost:11434/v1 and a vision model."
        )

    key = _pick(api_key, "API_KEY", None, str)
    if not key:
        key = os.environ.get("OPENAI_API_KEY") or PLACEHOLDER_API_KEY

    settings = Settings(
        base_url=base_url,
        model=model,
        api_key=key,
        max_file_mb=_pick(max_file_mb, "MAX_FILE_MB", MAX_FILE_MB, float),
        max_pages=_pick(max_pages, "MAX_PAGES", MAX_PAGES, int),
        max_files=_pick(max_files, "MAX_FILES", MAX_FILES, int),
        max_image_side=_pick(max_image_side, "MAX_IMAGE_SIDE", MAX_IMAGE_SIDE, int),
        pdf_render_scale=_pick(pdf_render_scale, "PDF_RENDER_SCALE", PDF_RENDER_SCALE, float),
        concurrency=_pick(concurrency, "CONCURRENCY", CONCURRENCY, int),
        timeout=_pick(timeout, "TIMEOUT", TIMEOUT_SECONDS, float),
        max_retries=_pick(max_retries, "MAX_RETRIES", MAX_RETRIES, int),
        prompt=_pick(prompt, "PROMPT", DEFAULT_PROMPT, str),
    )
    _validate(settings)
    return settings


def _validate(s: Settings) -> None:
    positive = {
        "max_file_mb": s.max_file_mb,
        "max_pages": s.max_pages,
        "max_files": s.max_files,
        "max_image_side": s.max_image_side,
        "pdf_render_scale": s.pdf_render_scale,
        "concurrency": s.concurrency,
        "timeout": s.timeout,
    }
    for name, value in positive.items():
        if value <= 0:
            raise ConfigError(f"{name} must be greater than 0, but is {value}.")
    if s.max_retries < 0:
        raise ConfigError("max_retries must not be negative.")
