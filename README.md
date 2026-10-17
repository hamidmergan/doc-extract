# doc-extract

A lightweight Python utility for extracting text as Markdown from images, scans and PDFs. Each page is sent to a vision model of your choice, and the recognized text comes back as Markdown. It does not depend on layout, language or document type.

doc-extract currently supports:

- PDF
- Images (PNG, JPG, WEBP, GIF, BMP, TIFF)

## Prerequisites

- Python 3.9 or newer
- A server with an OpenAI-compatible API and a **vision-capable model** (for example Ollama, vLLM, LM Studio, a university server or a cloud provider). A text-only model is not enough.
- An API key is optional. Many self-hosted servers do not need one.

If you run your own model, your documents stay on your own network. Nothing leaves your machine or data center.

## Installation

```bash
pip install doc-extract-llm
```

Alternatively, you can install it from the source:

```bash
git clone https://github.com/hamidmergan/doc-extract.git
cd doc-extract
pip install .
```

## Usage

### Command-Line

Print the result in the terminal:

```bash
doc-extract scan.pdf --stdout --base-url http://localhost:11434/v1 --model your-vision-model
```

With several files, each result gets a `<!-- file: name -->` header.

Write the result to a file instead:

```bash
doc-extract scan.pdf --base-url http://localhost:11434/v1 --model your-vision-model
```

This writes `scan.md` next to `scan.pdf`. Several files work the same way:

```bash
doc-extract a.pdf b.jpg --base-url http://localhost:11434/v1 --model your-vision-model
```

Use `-o` to choose the output. For one file it is a file, for several files it is a folder:

```bash
doc-extract scan.pdf -o notes/scan.md --base-url http://localhost:11434/v1 --model your-vision-model
doc-extract a.pdf b.jpg -o output/ --base-url http://localhost:11434/v1 --model your-vision-model
```

If two inputs share the same name without extension (for example `a.pdf` and `a.jpg`), the full name is used instead (`a.pdf.md`, `a.jpg.md`). If the target already exists, a number is added (`scan (1).md`, `scan (2).md`). A file named explicitly with `-o` is overwritten. Errors appear on stderr. The exit code is 1 if at least one file failed.

### Python API

```python
from doc_extract import extract

text = extract(
    "scan.pdf",
    base_url="http://localhost:11434/v1",
    model="your-vision-model",
)
print(text)
```

Several files, each handled on its own:

```python
from doc_extract import extract_many

results = extract_many(["a.pdf", "b.jpg"], base_url=..., model=...)
for name, result in results.items():
    if result.ok:
        print(name, result.text)
    else:
        print(name, "Error:", result.error)
```

`extract_many` keeps the input order. If one file fails, the others continue and the error is stored in that file's result.

For PDFs, a marker such as `<!-- page 2 -->` is placed before each page. Use `page_markers=False` to turn it off.

### Settings

Order: argument, then environment variable, then default.

| Argument / flag | Environment variable | Default |
| --- | --- | --- |
| `base_url` / `--base-url` | `DOC_EXTRACT_BASE_URL` | none, required |
| `model` / `--model` | `DOC_EXTRACT_MODEL` | none, required |
| `api_key` / `--api-key` | `DOC_EXTRACT_API_KEY` (then `OPENAI_API_KEY`) | optional |
| `max_file_mb` / `--max-file-mb` | `DOC_EXTRACT_MAX_FILE_MB` | 20 |
| `max_pages` / `--max-pages` | `DOC_EXTRACT_MAX_PAGES` | 50 |
| `max_files` / `--max-files` | `DOC_EXTRACT_MAX_FILES` | 20 |
| `max_image_side` / `--max-image-side` | `DOC_EXTRACT_MAX_IMAGE_SIDE` | 2000 pixels |
| `concurrency` / `--concurrency` | `DOC_EXTRACT_CONCURRENCY` | 4 |
| `timeout` / `--timeout` | `DOC_EXTRACT_TIMEOUT` | 120 seconds |
| `prompt` / `--prompt` | `DOC_EXTRACT_PROMPT` | default prompt |

If a limit is exceeded, the file is rejected with a message naming the limit and the setting. Nothing is silently truncated. Only oversized images are downscaled before sending (longest side `max_image_side`).

## Limitations

Quality depends on the chosen model. A small model may misread handwriting, poor photos and very dense tables. Check important results.

## Running Tests

```bash
pip install -e ".[test]"
pytest
```

The tests run against a local fake server and need no real model.

## License

MIT
