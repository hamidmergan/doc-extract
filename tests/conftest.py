import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest


class FakeServer:
    def __init__(self):
        self.requests = []
        self.fail_marker = None
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                outer.requests.append({"headers": {k.lower(): v for k, v in self.headers.items()}, "body": body})
                if outer.fail_marker:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b"{}")
                    return
                url = body["messages"][0]["content"][1]["image_url"]["url"]
                text = f"text-{len(url) % 1000}"
                payload = {
                    "id": "x",
                    "object": "chat.completion",
                    "created": 0,
                    "model": body["model"],
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {"role": "assistant", "content": text},
                        }
                    ],
                }
                data = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.httpd.server_port}/v1"

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def server():
    s = FakeServer()
    yield s
    s.stop()


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    import os

    for name in list(os.environ):
        if name.startswith("DOC_EXTRACT_") or name == "OPENAI_API_KEY":
            monkeypatch.delenv(name)


@pytest.fixture
def make_image(tmp_path):
    from PIL import Image

    def _make(name="a.png", size=(200, 100), color=(255, 255, 255)):
        path = tmp_path / name
        Image.new("RGB", size, color).save(path)
        return path

    return _make


@pytest.fixture
def make_pdf(tmp_path):
    import pypdfium2 as pdfium

    def _make(name="a.pdf", pages=2):
        pdf = pdfium.PdfDocument.new()
        for i in range(pages):
            pdf.new_page(200 + i * 10, 100)
        path = tmp_path / name
        pdf.save(str(path))
        pdf.close()
        return path

    return _make
