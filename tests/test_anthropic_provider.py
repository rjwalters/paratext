"""Anthropic provider tests.

These tests don't make any network calls. They cover the offline pieces:
system-message extraction, sampling-param stripping for Opus 4.7, and the
provider registry. End-to-end behavior with the real API requires
ANTHROPIC_API_KEY and is exercised via scripts, not the test suite.
"""

from __future__ import annotations

from paratext.providers import get_provider, parse_model_spec
from paratext.providers.anthropic_provider import (
    _model_supports_sampling_params,
    _split_system_and_messages,
)


def test_parse_model_spec_anthropic():
    assert parse_model_spec("anthropic/claude-opus-4-7") == (
        "anthropic",
        "claude-opus-4-7",
    )


def test_unknown_scheme_lists_anthropic():
    """The error message for an unknown scheme should advertise that anthropic
    is supported, not just mock and openai."""
    import pytest

    with pytest.raises(ValueError, match="anthropic"):
        get_provider("nonexistent_provider")


def test_split_system_extracts_first_system_message():
    msgs = [
        {"role": "system", "content": "you are an analyst"},
        {"role": "user", "content": "hi"},
    ]
    system, rest = _split_system_and_messages(msgs)
    assert system == "you are an analyst"
    assert rest == [{"role": "user", "content": "hi"}]


def test_split_system_returns_none_when_absent():
    msgs = [{"role": "user", "content": "hi"}]
    system, rest = _split_system_and_messages(msgs)
    assert system is None
    assert rest == [{"role": "user", "content": "hi"}]


def test_split_system_only_first_system_message_is_extracted():
    """If a caller passes multiple system messages (unusual), only the first
    is hoisted out — subsequent ones stay in the message list as-is."""
    msgs = [
        {"role": "system", "content": "first"},
        {"role": "user", "content": "hi"},
        {"role": "system", "content": "second"},
        {"role": "assistant", "content": "ok"},
    ]
    system, rest = _split_system_and_messages(msgs)
    assert system == "first"
    assert {"role": "system", "content": "second"} in rest


def test_opus_4_7_drops_sampling_params():
    assert _model_supports_sampling_params("claude-opus-4-7") is False
    assert _model_supports_sampling_params("claude-opus-4-7-20260101") is False
    # Case-insensitive match (defensive).
    assert _model_supports_sampling_params("Claude-Opus-4-7") is False


def test_other_models_keep_sampling_params():
    assert _model_supports_sampling_params("claude-opus-4-6") is True
    assert _model_supports_sampling_params("claude-sonnet-4-6") is True
    assert _model_supports_sampling_params("claude-haiku-4-5") is True
    assert _model_supports_sampling_params("claude-haiku-4-5-20251001") is True
