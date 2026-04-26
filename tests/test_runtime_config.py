from __future__ import annotations

from pathlib import Path

from llm.client import LLMClient, LLMResponse
from sdd.config.loader import load_runtime_config


def test_load_runtime_config_builds_legacy_compatible_shape():
    config = load_runtime_config()

    assert config["article"]["required_sections"]
    assert config["research"]["search_queries"]
    assert config["analysis"]["required_fields"]
    assert config["pipeline"]["timeout_total_seconds"] == 1800
    assert config["models"]["researcher"]
    assert config["model_providers"]["critic"] == "ollama"


def test_llm_client_uses_explicit_role_provider_not_model_name(monkeypatch):
    config = load_runtime_config()
    config["models"]["critic"] = "gemma4:26b"
    config["model_providers"]["critic"] = "openrouter"

    client = LLMClient(spec=config)

    def unexpected_ollama(**_kwargs):
        raise AssertionError("ollama should not be called first for critic")

    def fake_openrouter(**_kwargs):
        return LLMResponse("ok")

    monkeypatch.setattr(client, "generate_ollama", unexpected_ollama)
    monkeypatch.setattr(client, "generate_openrouter", fake_openrouter)

    response = client.generate(
        role="critic",
        model=config["models"]["critic"],
        prompt="teste",
        temperature=0.0,
        timeout=1,
    )

    assert response.response == "ok"


def test_validator_fixture_can_load_new_config_shape():
    config = load_runtime_config(Path("sdd/config"))
    assert "quality_rules" in config["article"]
