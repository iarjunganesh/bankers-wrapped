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
