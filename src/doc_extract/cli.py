import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .core import extract_many
from .errors import ExtractError


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="doc-extract",
        description="Extract text as Markdown from images and PDFs with a vision model.",
    )
    p.add_argument("files", nargs="+", help="Images or PDFs")
    p.add_argument(
        "-o",
        "--output",
        help="Output file (one input) or output folder (several inputs). "
        "Default: write <name>.md next to each input",
    )
    p.add_argument("--stdout", action="store_true", help="Print the result instead of writing files")
    p.add_argument("--base-url", help="URL of the OpenAI-compatible server, e.g. http://localhost:11434/v1")
    p.add_argument("--model", help="Name of the vision model")
    p.add_argument("--api-key", help="API key, if the server requires one")
    p.add_argument("--prompt", help="Custom instruction instead of the default prompt")
    p.add_argument("--no-page-markers", action="store_true", help="Do not add page markers for PDFs")
    p.add_argument("--max-file-mb", type=float)
    p.add_argument("--max-pages", type=int)
    p.add_argument("--max-files", type=int)
    p.add_argument("--max-image-side", type=int, help="Longest image side in pixels before sending")
    p.add_argument("--concurrency", type=int, help="Pages per file processed in parallel")
    p.add_argument("--timeout", type=float, help="Seconds per request")
    p.add_argument("--version", action="version", version=f"doc-extract {__version__}")
    return p


def _targets(keys: List[str], out: Optional[Path]) -> dict:
    """Map each input to its output file: <stem>.md, or <name>.md if two stems would collide."""
    stems = [Path(k).stem for k in keys]
    unique = len(set(stems)) == len(stems)
    targets = {}
    for key in keys:
        path = Path(key)
        name = (path.stem if unique else path.name) + ".md"
        targets[key] = (out / name) if out is not None else path.with_name(name)
    return targets


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    many = len(args.files) > 1
    out = Path(args.output) if args.output else None

    if args.stdout and out is not None:
        print("--stdout and -o cannot be combined.", file=sys.stderr)
        return 2

    if many and out is not None and out.exists() and not out.is_dir():
        print("With several files, -o must be a folder.", file=sys.stderr)
        return 2

    try:
        results = extract_many(
            args.files,
            base_url=args.base_url,
            model=args.model,
            api_key=args.api_key,
            prompt=args.prompt,
            page_markers=not args.no_page_markers,
            max_file_mb=args.max_file_mb,
            max_pages=args.max_pages,
            max_files=args.max_files,
            max_image_side=args.max_image_side,
            concurrency=args.concurrency,
            timeout=args.timeout,
        )
    except ExtractError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    failed = 0
    targets = _targets(list(results), out if many else None)
    if many and out is not None:
        out.mkdir(parents=True, exist_ok=True)

    for key, result in results.items():
        if not result.ok:
            failed += 1
            print(f"Error for {key}: {result.error}", file=sys.stderr)
            continue
        if args.stdout:
            if many:
                print(f"<!-- file: {Path(key).name} -->")
            print(result.text)
            if many:
                print()
            continue
        target = out if (out is not None and not many) else targets[key]
        target.write_text(result.text + "\n", encoding="utf-8")
        print(f"Wrote {target}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
