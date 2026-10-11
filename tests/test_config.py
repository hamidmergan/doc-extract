import pytest

from doc_extract import config
from doc_extract.errors import ConfigError


def test_missing_base_url_and_model_gives_clear_error():
    with pytest.raises(ConfigError) as e:
        config.resolve()
    assert "base_url" in str(e.value) and "model" in str(e.value)


def test_api_key_optional_uses_placeholder():
    s = config.resolve(base_url="http://x/v1", model="m")
    assert s.api_key == config.PLACEHOLDER_API_KEY


def test_precedence_arg_env_default(monkeypatch):
    monkeypatch.setenv("DOC_EXTRACT_MAX_PAGES", "7")
    base = dict(base_url="http://x/v1", model="m")
    assert config.resolve(**base).max_pages == 7
    assert config.resolve(max_pages=3, **base).max_pages == 3
    monkeypatch.delenv("DOC_EXTRACT_MAX_PAGES")
    assert config.resolve(**base).max_pages == config.MAX_PAGES


def test_env_for_connection(monkeypatch):
    monkeypatch.setenv("DOC_EXTRACT_BASE_URL", "http://h/v1")
    monkeypatch.setenv("DOC_EXTRACT_MODEL", "mm")
    monkeypatch.setenv("DOC_EXTRACT_API_KEY", "k")
    s = config.resolve()
    assert (s.base_url, s.model, s.api_key) == ("http://h/v1", "mm", "k")


def test_invalid_env_value(monkeypatch):
    monkeypatch.setenv("DOC_EXTRACT_MAX_PAGES", "abc")
    with pytest.raises(ConfigError):
        config.resolve(base_url="http://x/v1", model="m")


def test_non_positive_limit_rejected():
    with pytest.raises(ConfigError):
        config.resolve(base_url="http://x/v1", model="m", max_pages=0)
