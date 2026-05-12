import pytest
from app.config.agents import AgentLLMConfig, AgentsConfig

@pytest.fixture
def valid_llm_config():
    return AgentLLMConfig(
        model="gpt-4o-mini",
        model_provider="openai",
        temperature=0.7,
        max_tokens=4096,
    )

@pytest.fixture
def valid_agents_config(valid_llm_config):
    return AgentsConfig(
        planner=valid_llm_config,
        research=valid_llm_config,
        reviewer=valid_llm_config,
        synthesizer=valid_llm_config,
    )

@pytest.fixture
def fallback_llm_config():
    return AgentLLMConfig(
        model="gpt-4o-mini",
        model_provider="openai",
        temperature=0.7,
        max_tokens=4096,
        fallback_model="gpt-3.5-turbo",
        fallback_model_provider="openai",
    )
