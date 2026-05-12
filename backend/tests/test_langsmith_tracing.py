"""LangSmith tracing setup and chat run metadata."""

from __future__ import annotations

import os
from uuid import UUID

import pytest

from app.config.agents import AgentsConfig
from app.core.agent_factory import configure_langsmith_tracing
from app.services.chat_service import build_chat_graph_run_config


@pytest.fixture(autouse=True)
def _clear_LANGSMITH_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("LANGSMITH_TRACING_V2", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
        monkeypatch.delenv(key, raising=False)


def _agents_config(**overrides: object) -> AgentsConfig:
    return AgentsConfig.model_construct(**overrides)


def test_configure_langsmith_tracing_sets_env_when_enabled() -> None:
    agents = _agents_config(
        langsmith_tracing_enabled=True,
        langsmith_api_key="ls-test-key",
        langsmith_project="quorum-dev",
    )

    configure_langsmith_tracing(agents)

    assert os.environ["LANGSMITH_TRACING_V2"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "ls-test-key"
    assert os.environ["LANGSMITH_PROJECT"] == "quorum-dev"


def test_configure_langsmith_tracing_noop_when_disabled() -> None:
    agents = _agents_config(
        langsmith_tracing_enabled=False,
        langsmith_api_key="ls-test-key",
    )

    configure_langsmith_tracing(agents)

    assert "LANGSMITH_TRACING_V2" not in os.environ
    assert "LANGSMITH_API_KEY" not in os.environ


def test_build_chat_graph_run_config_includes_user_and_conversation_metadata() -> None:
    user_id = UUID("11111111-1111-4111-8111-111111111111")
    conversation_id = UUID("22222222-2222-4222-8222-222222222222")

    cfg = build_chat_graph_run_config(user_id=user_id, conversation_id=conversation_id)

    assert cfg["metadata"] == {
        "user_id": str(user_id),
        "conversation_id": str(conversation_id),
    }
    assert cfg["tags"] == ["chat", "executive_briefing"]
    assert cfg["run_name"] == f"chat:{conversation_id}"


def test_build_chat_graph_run_config_omits_metadata_without_ids() -> None:
    cfg = build_chat_graph_run_config()

    assert "metadata" not in cfg
    assert "tags" not in cfg
    assert "run_name" not in cfg
    assert cfg["recursion_limit"] == 200
