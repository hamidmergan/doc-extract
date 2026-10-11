# doc-extract

Extract text as Markdown from images, scans and PDFs. The tool sends each page to a vision model and returns the recognized text. It does not depend on layout, language or document type: any image and any PDF works.

## Requirements

- Python 3.9 or newer
- A server with an OpenAI-compatible API and a **vision-capable model** (for example Ollama, vLLM, LM Studio, a university server or a cloud provider). A text-only model is not enough.
- An API key is optional. Many self-hosted servers do not need one.

If you run your own model, your documents stay on your own network. Nothing leaves your machine or data center.

## Installation

Into your own project (activate the project's virtual environment first):

```
pip install git+https://github.com/hamidmergan/doc-extract.git
```

From source, to try it out or to develop:

```
git clone https://github.com/hamidmergan/doc-extract.git
cd doc-extract
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install .
```

A virtual environment keeps the install separate from your system Python. Some systems (recent macOS and Linux with system or Homebrew Python) refuse `pip install` outside one. Activate it again in each new terminal before using `doc-extract`.

## Library usage

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

## Command line usage

```
doc-extract scan.pdf --base-url http://localhost:11434/v1 --model your-vision-model
doc-extract scan.pdf -o scan.md
doc-extract a.pdf b.jpg -o output/
```

With several files, `-o` must be a folder. It receives one file per input, named with the full input name plus `.md`, for example `a.pdf.md` and `b.jpg.md`. Without `-o`, everything goes to stdout, with a `<!-- file: name -->` header when there are several files. Errors appear on stderr. The exit code is 1 if at least one file failed.

## Settings

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

Supported formats: PDF, PNG, JPG, WEBP, GIF, BMP and TIFF.

## Limitations

Quality depends on the chosen model. A small model may misread handwriting, poor photos and very dense tables. Check important results.

## Tests

```
pip install -e ".[test]"
pytest
```

The tests run against a local fake server and need no real model.

## License

MIT
