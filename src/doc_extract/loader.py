"""Validate files and convert them into single page images (PNG bytes)."""

import io
from pathlib import Path
from typing import List, Union

from .config import Settings
from .errors import LimitError, UnsupportedFileError

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
PDF_SUFFIX = ".pdf"


def supported_suffixes() -> List[str]:
    return sorted(IMAGE_SUFFIXES | {PDF_SUFFIX})


def check_file(path: Path, settings: Settings) -> None:
    if not path.is_file():
        raise UnsupportedFileError(f"File not found: {path}")
    suffix = path.suffix.lower()
    if suffix != PDF_SUFFIX and suffix not in IMAGE_SUFFIXES:
        raise UnsupportedFileError(
            f"File type {suffix or '(no extension)'} is not supported. "
            f"Allowed: {', '.join(supported_suffixes())}"
        )
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > settings.max_file_mb:
        raise LimitError(
            f"{path.name} is {size_mb:.1f} MB. The limit is "
            f"{settings.max_file_mb:g} MB (max_file_mb)."
        )


def load_pages(path: Union[str, Path], settings: Settings) -> List[bytes]:
    """Return one PNG per page. An image yields exactly one page."""
    path = Path(path)
    check_file(path, settings)
    if path.suffix.lower() == PDF_SUFFIX:
        return _pdf_pages(path, settings)
    return [_image_page(path, settings)]


def _to_png(image, max_side: int) -> bytes:
    from PIL import Image

    if image.mode not in ("RGB", "L"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        rgba = image.convert("RGBA")
        background.paste(rgba, mask=rgba.split()[-1])
        image = background
    longest = max(image.size)
    if longest > max_side:
        factor = max_side / longest
        new_size = (max(1, round(image.width * factor)), max(1, round(image.height * factor)))
        image = image.resize(new_size, Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _image_page(path: Path, settings: Settings) -> bytes:
    from PIL import Image, ImageOps

    try:
        with Image.open(path) as image:
            image.load()
            image = ImageOps.exif_transpose(image)
            return _to_png(image, settings.max_image_side)
    except (OSError, ValueError) as exc:
        raise UnsupportedFileError(f"{path.name} cannot be read as an image: {exc}")


def _pdf_pages(path: Path, settings: Settings) -> List[bytes]:
    import pypdfium2 as pdfium

    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception as exc:
        raise UnsupportedFileError(f"{path.name} cannot be read as a PDF: {exc}")
    try:
        count = len(pdf)
        if count > settings.max_pages:
            raise LimitError(
                f"{path.name} has {count} pages. The limit is "
                f"{settings.max_pages} (max_pages)."
            )
        pages = []
        for index in range(count):
            page = pdf[index]
            try:
                bitmap = page.render(scale=settings.pdf_render_scale)
                pages.append(_to_png(bitmap.to_pil(), settings.max_image_side))
            finally:
                page.close()
        return pages
    finally:
        pdf.close()
