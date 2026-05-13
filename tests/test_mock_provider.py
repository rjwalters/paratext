"""Mock provider tests."""

from __future__ import annotations

import json

from textual_intuition.providers import get_provider, parse_model_spec
from textual_intuition.providers.mock import MockProvider


def test_parse_model_spec():
    assert parse_model_spec("mock/echo") == ("mock", "echo")
    assert parse_model_spec("openai/gpt-4o-mini") == ("openai", "gpt-4o-mini")


def test_get_provider_mock():
    p = get_provider("mock")
    assert isinstance(p, MockProvider)


def test_explicit_payload_is_valid_json_with_expected_keys():
    p = MockProvider()
    messages = [
        {"role": "system", "content": "You are an analyst inferring latent state."},
        {"role": "user", "content": "ok so ... i keep messing this up not sure if im asking right"},
    ]
    resp = p.complete(messages=messages, model="echo", experiment="explicit_state")
    obj = json.loads(resp.text)
    for key in ("fatigue", "rushed_or_mobile", "frustration", "confidence", "evidence"):
        assert key in obj


def test_mock_fatigue_cue_raises_fatigue_score():
    p = MockProvider()
    fatigue_msgs = [
        {"role": "system", "content": "latent"},
        {"role": "user", "content": "ok so ... i keep messing this up brain is mush"},
    ]
    polished_msgs = [
        {"role": "system", "content": "latent"},
        {"role": "user", "content": "Could you walk me through this carefully?"},
    ]
    f = json.loads(p.complete(messages=fatigue_msgs, model="echo").text)
    n = json.loads(p.complete(messages=polished_msgs, model="echo").text)
    assert f["fatigue"] > n["fatigue"]


def test_mock_implicit_response_shortens_under_fatigue():
    p = MockProvider()
    fatigue_msgs = [
        {"role": "system", "content": "answer normally"},
        {"role": "user", "content": "ok so ... i keep messing this up brain is mush"},
    ]
    neutral_msgs = [
        {"role": "system", "content": "answer normally"},
        {"role": "user", "content": "Could you walk me through this carefully?"},
    ]
    f = p.complete(messages=fatigue_msgs, model="echo", experiment="implicit_response").text
    n = p.complete(messages=neutral_msgs, model="echo", experiment="implicit_response").text
    assert len(f) < len(n)
