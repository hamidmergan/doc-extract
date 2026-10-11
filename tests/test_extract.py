import io

import pytest
from PIL import Image

from doc_extract import extract, extract_many
from doc_extract.errors import ConfigError, LimitError, ModelError, UnsupportedFileError


def conn(server):
    return dict(base_url=server.base_url, model="vision-test")


def test_image_single_request(server, make_image):
    text = extract(make_image(), **conn(server))
    assert text.startswith("text-")
    assert len(server.requests) == 1
    body = server.requests[0]["body"]
    assert body["model"] == "vision-test"
    assert body["temperature"] == 0
    assert body["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_works_without_api_key(server, make_image):
    extract(make_image(), **conn(server))
    assert "not-needed" in server.requests[0]["headers"]["authorization"]


def test_works_with_api_key(server, make_image):
    extract(make_image(), api_key="secret", **conn(server))
    assert "secret" in server.requests[0]["headers"]["authorization"]


def test_pdf_pages_in_order_with_markers(server, make_pdf):
    text = extract(make_pdf(pages=3), concurrency=3, **conn(server))
    markers = [line for line in text.splitlines() if line.startswith("<!-- page")]
    assert markers == ["<!-- page 1 -->", "<!-- page 2 -->", "<!-- page 3 -->"]
    assert len(server.requests) == 3


def test_page_markers_can_be_disabled(server, make_pdf):
    text = extract(make_pdf(pages=2), page_markers=False, **conn(server))
    assert "<!--" not in text


def test_page_order_matches_content(make_pdf):
    """Pages have different sizes; the fake returns the width."""
    import threading
    import time

    class Fake:
        class chat:
            class completions:
                @staticmethod
                def create(**kw):
                    import base64

                    url = kw["messages"][0]["content"][1]["image_url"]["url"]
                    png = base64.b64decode(url.split(",", 1)[1])
                    width = Image.open(io.BytesIO(png)).width
                    # early pages answer more slowly to provoke reordering
                    time.sleep(0.3 if width < 600 else 0)

                    class R:
                        choices = [type("C", (), {"message": type("M", (), {"content": f"w{width}"})})]

                    return R

    text = extract(make_pdf(pages=3), client=Fake, base_url="x", model="m", concurrency=3, pdf_render_scale=2)
    widths = [l for l in text.splitlines() if l.startswith("w")]
    assert widths == sorted(widths, key=lambda w: int(w[1:]))
    assert len(widths) == 3


def test_large_image_is_downscaled(server, make_image):
    import base64

    path = make_image("big.png", size=(4000, 1000))
    extract(path, max_image_side=1000, **conn(server))
    url = server.requests[0]["body"]["messages"][0]["content"][1]["image_url"]["url"]
    img = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert max(img.size) == 1000


def test_limit_file_size(server, make_image):
    with pytest.raises(LimitError) as e:
        extract(make_image(), max_file_mb=0.000001, **conn(server))
    assert "max_file_mb" in str(e.value)


def test_limit_pages(server, make_pdf):
    with pytest.raises(LimitError) as e:
        extract(make_pdf(pages=3), max_pages=2, **conn(server))
    assert "max_pages" in str(e.value)
    assert server.requests == []


def test_unsupported_type(server, tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("hi")
    with pytest.raises(UnsupportedFileError):
        extract(f, **conn(server))


def test_corrupt_image(server, tmp_path):
    f = tmp_path / "bad.png"
    f.write_bytes(b"not an image")
    with pytest.raises(UnsupportedFileError):
        extract(f, **conn(server))


def test_corrupt_pdf(server, tmp_path):
    f = tmp_path / "bad.pdf"
    f.write_bytes(b"not a pdf")
    with pytest.raises(UnsupportedFileError):
        extract(f, **conn(server))


def test_missing_config():
    with pytest.raises(ConfigError):
        extract("whatever.png")


def test_server_error_is_model_error(server, make_image):
    server.fail_marker = True
    with pytest.raises(ModelError):
        extract(make_image(), max_retries=0, **conn(server))


def test_many_keyed_and_ordered(server, make_image, make_pdf):
    a, b, c = make_image("a.png"), make_pdf("b.pdf", pages=2), make_image("c.png")
    results = extract_many([c, a, b], **conn(server))
    assert list(results) == [str(c), str(a), str(b)]
    assert all(r.ok for r in results.values())
    assert "<!-- page 2 -->" in results[str(b)].text
    assert "<!--" not in results[str(a)].text


def test_many_one_failure_does_not_stop_rest(server, make_image, tmp_path):
    good1, good2 = make_image("g1.png"), make_image("g2.png")
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"nope")
    results = extract_many([good1, bad, good2], **conn(server))
    assert results[str(good1)].ok and results[str(good2)].ok
    assert not results[str(bad)].ok and "bad.png" in results[str(bad)].error


def test_many_file_count_limit(server, make_image):
    files = [make_image(f"{i}.png") for i in range(3)]
    with pytest.raises(LimitError) as e:
        extract_many(files, max_files=2, **conn(server))
    assert "max_files" in str(e.value)
    assert server.requests == []


def test_many_duplicates_rejected(server, make_image):
    f = make_image()
    with pytest.raises(LimitError):
        extract_many([f, f], **conn(server))
