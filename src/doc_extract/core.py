from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

from . import config
from .client import make_client, transcribe_page
from .errors import ExtractError, LimitError
from .loader import load_pages

PathLike = Union[str, Path]


@dataclass
class Result:
    path: str
    text: str = ""
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _page_marker(number: int) -> str:
    return f"<!-- page {number} -->"


def _join_pages(texts: List[str], page_markers: bool) -> str:
    if len(texts) == 1 or not page_markers:
        return "\n\n".join(t for t in texts if t)
    parts = []
    for number, text in enumerate(texts, start=1):
        parts.append(_page_marker(number) + ("\n\n" + text if text else ""))
    return "\n\n".join(parts)


def _extract_one(path: Path, settings: config.Settings, client, page_markers: bool) -> str:
    pages = load_pages(path, settings)
    workers = min(settings.concurrency, len(pages))
    if workers <= 1:
        texts = [transcribe_page(client, settings, png) for png in pages]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # map returns the results in input order
            texts = list(pool.map(lambda png: transcribe_page(client, settings, png), pages))
    return _join_pages(texts, page_markers)


def extract(
    path: PathLike,
    *,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    page_markers: bool = True,
    client=None,
    **limits,
) -> str:
    """Read text from an image or PDF and return it as Markdown.

    Errors are raised as exceptions (subclasses of ExtractError).
    Further settings (max_pages, max_file_mb, prompt, and so on)
    can be passed as keyword arguments.
    """
    settings = config.resolve(base_url=base_url, model=model, api_key=api_key, **limits)
    client = client or make_client(settings)
    return _extract_one(Path(path), settings, client, page_markers)


def extract_many(
    paths: Iterable[PathLike],
    *,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    page_markers: bool = True,
    client=None,
    **limits,
) -> Dict[str, Result]:
    """Process several files one by one and return a Result per file.

    The input order is preserved. If one file fails,
    the rest continues and the error is stored in that file's Result.
    """
    settings = config.resolve(base_url=base_url, model=model, api_key=api_key, **limits)
    path_list = [Path(p) for p in paths]
    if len(path_list) > settings.max_files:
        raise LimitError(
            f"{len(path_list)} files given. The limit is "
            f"{settings.max_files} (max_files)."
        )
    keys = [str(p) for p in path_list]
    if len(set(keys)) != len(keys):
        raise LimitError("The same file was given more than once.")

    client = client or make_client(settings)
    results: Dict[str, Result] = {}
    for path in path_list:
        key = str(path)
        try:
            results[key] = Result(key, text=_extract_one(path, settings, client, page_markers))
        except ExtractError as exc:
            results[key] = Result(key, error=str(exc))
    return results
