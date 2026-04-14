#!/usr/bin/env python3
"""Unit tests for Gemini client model selection and basic generation flow."""

from types import SimpleNamespace

from diary.gemini_client import DEFAULT_MODEL, GeminiClient


def _sample_bible_content():
    return {
        "date": "Sunday, September 1, 2025",
        "gospel_citation": "Matthew 5:3-8",
        "gospel_body": "Blessed are the poor in spirit, for theirs is the kingdom of heaven.",
    }


def test_default_model_is_gemini_3_flash_preview(monkeypatch):
    """Ensure the client uses gemini-3-flash-preview by default."""
    captured = {"configured_key": None, "model_name": None}

    def fake_configure(api_key):
        captured["configured_key"] = api_key

    class FakeModel:
        def __init__(self, name):
            captured["model_name"] = name

        def generate_content(self, *_args, **_kwargs):
            return SimpleNamespace(text="ok")

    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr("diary.gemini_client.genai.configure", fake_configure)
    monkeypatch.setattr("diary.gemini_client.genai.GenerativeModel", FakeModel)

    client = GeminiClient("fake-key")
    assert client.model_name == DEFAULT_MODEL
    assert captured["configured_key"] == "fake-key"
    assert captured["model_name"] == "gemini-3-flash-preview"


def test_env_model_overrides_default(monkeypatch):
    """Ensure GEMINI_MODEL overrides the default model."""
    captured = {"model_name": None}

    class FakeModel:
        def __init__(self, name):
            captured["model_name"] = name

        def generate_content(self, *_args, **_kwargs):
            return SimpleNamespace(text="ok")

    monkeypatch.setenv("GEMINI_MODEL", "custom-test-model")
    monkeypatch.setattr("diary.gemini_client.genai.configure", lambda api_key: None)
    monkeypatch.setattr("diary.gemini_client.genai.GenerativeModel", FakeModel)

    client = GeminiClient("fake-key")
    assert client.model_name == "custom-test-model"
    assert captured["model_name"] == "custom-test-model"


def test_generate_diary_entry_returns_text_from_model(monkeypatch):
    """Ensure generated text is returned when the model provides a valid response."""

    class FakeModel:
        def __init__(self, _name):
            pass

        def generate_content(self, *_args, **_kwargs):
            candidate = SimpleNamespace(
                finish_reason=1,
                content=SimpleNamespace(parts=[SimpleNamespace(text="Generated diary content")]),
            )
            return SimpleNamespace(candidates=[candidate])

    monkeypatch.setattr("diary.gemini_client.genai.configure", lambda api_key: None)
    monkeypatch.setattr("diary.gemini_client.genai.GenerativeModel", FakeModel)

    client = GeminiClient("fake-key")
    result = client.generate_diary_entry(_sample_bible_content())
    assert result == "Generated diary content"


def test_format_bible_content_contains_vietnamese_section_when_present(monkeypatch):
    """Ensure formatted content includes Vietnamese verses when enrichment provides them."""

    class FakeModel:
        def __init__(self, _name):
            pass

        def generate_content(self, *_args, **_kwargs):
            return SimpleNamespace(text="ok")

    monkeypatch.setattr("diary.gemini_client.genai.configure", lambda api_key: None)
    monkeypatch.setattr("diary.gemini_client.genai.GenerativeModel", FakeModel)

    client = GeminiClient("fake-key")
    monkeypatch.setattr(
        client,
        "_enrich_with_vietnamese_verses",
        lambda content: {
            **content,
            "vietnamese_gospel": "Phuc thay ai co tam hon ngheo kho",
            "gospel_reference": "Matthew 5:3",
        },
    )

    content = _sample_bible_content()
    formatted = client._format_bible_content(content)

    assert "Tiếng Việt (Matthew 5:3):" in formatted
    assert "Phuc thay ai co tam hon ngheo kho" in formatted
