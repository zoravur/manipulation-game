import os
from pathlib import Path

import pytest

import openrouter_sample as ors


def test_compute_request_hash_stable():
    messages = [
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "Hi"},
    ]
    params = {
        "model": "openai/gpt-4o-mini",
        "tools": [],
        "tool_choice": "none",
        "max_tokens": 256,
    }

    first = ors.compute_request_hash(messages, params, 1234)
    second = ors.compute_request_hash(messages, params, 1234)
    assert first == second

    params_changed = {**params, "model": "openai/gpt-5.2"}
    third = ors.compute_request_hash(messages, params_changed, 1234)
    assert third != first


def test_cache_roundtrip(tmp_path: Path):
    cache = ors.ResponseCache(tmp_path / "cache.sqlite3")
    cache.set("abc", {"content": "ok", "tool_calls": []})
    assert cache.get("abc") == {"content": "ok", "tool_calls": []}


def test_cached_response_without_api_key(tmp_path: Path, monkeypatch):
    cache = ors.ResponseCache(tmp_path / "cache.sqlite3")
    monkeypatch.setattr(ors, "CACHE", cache)
    monkeypatch.setattr(ors, "LOG_FILE", tmp_path / "log.jsonl")

    prompt = "Say hello."
    messages = [
        {"role": "system", "content": "Provide concise steps; use tools if helpful."},
        {"role": "user", "content": prompt},
    ]
    params = {
        "model": "openai/gpt-4o-mini",
        "tools": [],
        "tool_choice": "none",
        "max_tokens": 256,
    }
    request_hash = ors.compute_request_hash(messages, params, ors.REQUEST_SEED)
    cache.set(request_hash, {"content": "cached response", "tool_calls": []})

    result = ors.chat_with_tools(
        "openai/gpt-4o-mini",
        prompt,
        [],
        tool_choice="none",
    )
    assert result == "cached response"


@pytest.mark.integration
def test_live_request_roundtrip(tmp_path: Path, monkeypatch):
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")

    cache = ors.ResponseCache(tmp_path / "cache.sqlite3")
    monkeypatch.setattr(ors, "CACHE", cache)
    monkeypatch.setattr(ors, "LOG_FILE", tmp_path / "log.jsonl")

    prompt = "Say hello in one sentence."
    model = os.getenv("OPENROUTER_TEST_MODEL", "openai/gpt-4o-mini")
    result = ors.chat_with_tools(model, prompt, [], tool_choice="none")
    assert result.strip()

    messages = [
        {"role": "system", "content": "Provide concise steps; use tools if helpful."},
        {"role": "user", "content": prompt},
    ]
    params = {
        "model": model,
        "tools": [],
        "tool_choice": "none",
        "max_tokens": 256,
    }
    request_hash = ors.compute_request_hash(messages, params, ors.REQUEST_SEED)
    assert cache.get(request_hash) is not None
