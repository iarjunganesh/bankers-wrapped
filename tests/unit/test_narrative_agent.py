"""Unit tests for NarrativeAgent (SDK-only Genblaze routing)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.analytics_agent import AnalyticsAgentOutput
from backend.agents.narrative_agent import NarrativeAgent
from backend.config import Settings
from backend.media.genblaze_client import ScriptResult
from backend.models.insights import (
    CategorySpend,
    FinancialInsights,
    FinancialPersonality,
)

MOCK_SCRIPT_RESPONSE = json.dumps(
    {
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
    }
)


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


def _settings(provider: str = "genblaze") -> Settings:
    return Settings(
        narrative_provider=provider,
        gmi_chat_model="meta-llama/Llama-3.3-70B-Instruct",
        nvidia_nim_model="meta/llama-3.1-70b-instruct",
        gmi_api_key="mock-gmi",
        nvidia_nim_api_key="nvapi-test",
        openai_api_key="sk-test",
    )


def _script_result(
    text: str,
    model: str = "meta-llama/Llama-3.3-70B-Instruct",
    provider: str = "gmi-cloud",
) -> ScriptResult:
    return ScriptResult(
        text=text,
        model=model,
        provider=provider,
        latency_ms=1200,
        retry_count=0,
        tokens_in=900,
        tokens_out=450,
        cost_usd=0.0012,
    )


class TestNarrativeAgentSdkOnly:
    def test_requires_genblaze_client(self):
        with pytest.raises(ValueError, match="requires GenblazeClient"):
            NarrativeAgent(_settings(), genblaze=None)

    async def test_uses_sdk_and_returns_script(self):
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock(return_value=_script_result(MOCK_SCRIPT_RESPONSE))
        agent = NarrativeAgent(_settings(), genblaze=genblaze)

        output = await agent(make_analytics_output())

        genblaze.generate_script_text.assert_called_once()
        assert len(output.script.scenes) == 4
        assert output.llm["provider"] == "gmi-cloud"
        assert output.llm["label"] == "gmi-cloud/meta-llama/Llama-3.3-70B-Instruct"

    async def test_retries_invalid_json_then_fails(self):
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock(return_value=_script_result("NOT VALID JSON {{{"))
        agent = NarrativeAgent(_settings(), genblaze=genblaze)

        with pytest.raises(RuntimeError, match="failed via Genblaze SDK"):
            await agent(make_analytics_output())

        assert genblaze.generate_script_text.call_count == 2

    async def test_retries_provider_error_then_fails(self):
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock(side_effect=RuntimeError("GMI down"))
        agent = NarrativeAgent(_settings(), genblaze=genblaze)

        with pytest.raises(RuntimeError, match="failed via Genblaze SDK"):
            await agent(make_analytics_output())

        assert genblaze.generate_script_text.call_count == 2

    async def test_nvidia_mode_routes_through_sdk_with_nim_model(self):
        genblaze = MagicMock()
        genblaze.generate_script_text = AsyncMock(
            return_value=_script_result(
                MOCK_SCRIPT_RESPONSE,
                model="nvidia-nim/meta/llama-3.1-70b-instruct",
                provider="nvidia-nim",
            )
        )
        agent = NarrativeAgent(_settings(provider="nvidia-nim"), genblaze=genblaze)

        output = await agent(make_analytics_output())

        kwargs = genblaze.generate_script_text.call_args.kwargs
        assert kwargs["model"] == "nvidia-nim/meta/llama-3.1-70b-instruct"
        assert output.llm["provider"] == "nvidia-nim"
        assert output.llm["label"] == "nvidia-nim/meta/llama-3.1-70b-instruct"
