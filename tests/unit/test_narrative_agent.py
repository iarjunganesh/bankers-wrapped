"""Unit tests for NarrativeAgent — mocks OpenAI."""

import json

import pytest

from backend.agents.analytics_agent import AnalyticsAgentOutput
from backend.agents.narrative_agent import NarrativeAgent
from backend.models.insights import (
    CategorySpend,
    FinancialInsights,
    FinancialPersonality,
)

MOCK_GPT_RESPONSE = json.dumps({
    "title": "Your January Financial Journey",
    "personality": "Financial Builder",
    "scenes": [
        {
            "id": 1,
            "narration": "You are a Financial Builder. January was a month of discipline and progress.",
            "visual_prompt": "A minimalist chart showing upward savings growth, blue tones",
        },
        {
            "id": 2,
            "narration": "Your savings rate reached 9.2%, reflecting consistent financial habits.",
            "visual_prompt": "Abstract coins stacking into a pillar, warm golden light",
        },
        {
            "id": 3,
            "narration": "Travel was your largest discretionary spend at 24% of expenses.",
            "visual_prompt": "Minimalist airplane silhouette over a world map, muted colours",
        },
        {
            "id": 4,
            "narration": "Keep building. Your foundation is getting stronger every month.",
            "visual_prompt": "Clean upward arrow graphic on a gradient background",
        },
    ],
})


def make_analytics_output() -> AnalyticsAgentOutput:
    return AnalyticsAgentOutput(
        insights=FinancialInsights(
            period_label="January 2026",
            total_income=13000.0,
            total_expenses=1840.4,
            savings_amount=1200.0,
            savings_rate=9.2,
            top_categories=[
                CategorySpend(category="travel", amount=312.0, percentage=24.0),
                CategorySpend(category="food", amount=223.4, percentage=17.2),
                CategorySpend(category="housing", amount=12000.0, percentage=13.1),
            ],
            achievements=["Maintained a healthy 9.2% savings rate"],
            personality=FinancialPersonality.BUILDER,
            personality_reason="High savings rate.",
            currency="USD",
        )
    )


@pytest.fixture
def mock_openai(mocker):
    mock = mocker.patch("backend.agents.narrative_agent.AsyncOpenAI")
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = MOCK_GPT_RESPONSE
    mock.return_value.chat.completions.create = mocker.AsyncMock(
        return_value=mock_response
    )
    return mock


class TestNarrativeAgent:
    async def test_returns_4_scenes(self, test_settings, mock_openai):
        agent = NarrativeAgent(test_settings)
        output = await agent(make_analytics_output())
        assert len(output.script.scenes) == 4

    async def test_title_non_empty(self, test_settings, mock_openai):
        agent = NarrativeAgent(test_settings)
        output = await agent(make_analytics_output())
        assert len(output.script.title) > 0

    async def test_personality_preserved(self, test_settings, mock_openai):
        agent = NarrativeAgent(test_settings)
        output = await agent(make_analytics_output())
        assert "Builder" in output.script.personality

    async def test_each_scene_has_narration(self, test_settings, mock_openai):
        agent = NarrativeAgent(test_settings)
        output = await agent(make_analytics_output())
        for scene in output.script.scenes:
            assert len(scene.narration) > 0

    async def test_each_scene_has_visual_prompt(self, test_settings, mock_openai):
        agent = NarrativeAgent(test_settings)
        output = await agent(make_analytics_output())
        for scene in output.script.scenes:
            assert len(scene.visual_prompt) > 0

    async def test_full_narration_concatenates(self, test_settings, mock_openai):
        agent = NarrativeAgent(test_settings)
        output = await agent(make_analytics_output())
        full = output.script.full_narration
        assert "Financial Builder" in full


# ── WS-1: Genblaze LLM routing (ADR-007) ─────────────────────────────────────

from unittest.mock import AsyncMock, MagicMock  # noqa: E402

from backend.config import Settings  # noqa: E402
from backend.media.genblaze_client import ScriptResult  # noqa: E402


def _ws1_settings(provider: str = "genblaze") -> Settings:
    """Hermetic settings — every field the agent reads is explicit."""
    return Settings(
        narrative_provider=provider,
        gmi_chat_model="meta-llama/Llama-3.3-70B-Instruct",
        nvidia_nim_api_key="nvapi-test",
        openai_api_key="sk-test",
        gmi_api_key="mock-gmi",
    )


def _script_result(text: str) -> ScriptResult:
    return ScriptResult(
        text=text,
        model="meta-llama/Llama-3.3-70B-Instruct",
        latency_ms=1200,
        retry_count=0,
        tokens_in=900,
        tokens_out=450,
        cost_usd=0.0012,
    )


def _direct_path_mock(agent: NarrativeAgent) -> AsyncMock:
    """Mock the OpenAI-compatible fallback path on an already-built agent."""
    response = MagicMock()
    response.choices[0].message.content = MOCK_GPT_RESPONSE
    create = AsyncMock(return_value=response)
    agent.client = MagicMock()
    agent.client.chat.completions.create = create
    return create


class TestGenblazeRouting:
    async def test_narrative_agent_uses_genblaze_when_configured(self, mocker):
        mocker.patch("backend.agents.narrative_agent.AsyncOpenAI")
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock(
            return_value=_script_result(MOCK_GPT_RESPONSE)
        )
        agent = NarrativeAgent(_ws1_settings(), genblaze=genblaze)
        direct = _direct_path_mock(agent)

        output = await agent(make_analytics_output())

        genblaze.generate_script_text.assert_called_once()
        direct.assert_not_called()
        assert output.llm["provider"] == "gmi-cloud"
        assert output.llm["label"] == "gmi-cloud/meta-llama/Llama-3.3-70B-Instruct"
        assert output.llm["cost_usd"] == 0.0012
        assert len(output.script.scenes) == 4

    async def test_narrative_agent_falls_back_to_nim_on_invalid_json(self, mocker):
        mocker.patch("backend.agents.narrative_agent.AsyncOpenAI")
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock(
            return_value=_script_result("NOT VALID JSON {{{")
        )
        agent = NarrativeAgent(_ws1_settings(), genblaze=genblaze)
        direct = _direct_path_mock(agent)

        output = await agent(make_analytics_output())

        # invalid JSON is retried once, then the direct NIM path takes over
        assert genblaze.generate_script_text.call_count == 2
        direct.assert_called_once()
        assert output.llm["provider"] == "nvidia-nim"
        assert output.llm["label"] == "nvidia-nim/meta/llama-3.1-70b-instruct"
        assert len(output.script.scenes) == 4

    async def test_narrative_agent_falls_back_when_genblaze_raises(self, mocker):
        mocker.patch("backend.agents.narrative_agent.AsyncOpenAI")
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock(side_effect=RuntimeError("GMI down"))
        agent = NarrativeAgent(_ws1_settings(), genblaze=genblaze)
        direct = _direct_path_mock(agent)

        output = await agent(make_analytics_output())

        direct.assert_called_once()
        assert output.llm["provider"] == "nvidia-nim"

    async def test_default_provider_never_touches_genblaze(self, mocker):
        mocker.patch("backend.agents.narrative_agent.AsyncOpenAI")
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock()
        agent = NarrativeAgent(_ws1_settings(provider="nvidia-nim"), genblaze=genblaze)
        direct = _direct_path_mock(agent)

        output = await agent(make_analytics_output())

        genblaze.generate_script_text.assert_not_called()
        direct.assert_called_once()
        assert output.llm["provider"] == "nvidia-nim"
