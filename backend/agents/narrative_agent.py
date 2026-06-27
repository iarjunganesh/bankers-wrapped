"""
Narrative Agent.

Transforms FinancialInsights into a structured NarrativeScript (4 scenes)
using GPT-4o. The script is the input to the Media Agent.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import structlog
from openai import AsyncOpenAI

from backend.agents.analytics_agent import AnalyticsAgentOutput
from backend.agents.base import BaseAgent
from backend.config import Settings
from backend.models.narrative import NarrativeScript, Scene

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
log = structlog.get_logger()


@dataclass
class NarrativeAgentOutput:
    script: NarrativeScript


class NarrativeAgent(BaseAgent):
    """Generates a structured 4-scene video script from financial insights."""

    def __init__(self, settings: Settings) -> None:
        super().__init__("NarrativeAgent")
        self.settings = settings

        if settings.nvidia_nim_api_key:
            # NVIDIA NIM is OpenAI-API-compatible — just swap the base_url and key
            self.client = AsyncOpenAI(
                api_key=settings.nvidia_nim_api_key,
                base_url=settings.nvidia_nim_base_url,
            )
            self._model = settings.nvidia_nim_model
            self.log.info("narrative_agent.provider", provider="nvidia-nim", model=self._model)
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self._model = settings.openai_model
            self.log.info("narrative_agent.provider", provider="openai", model=self._model)

        self._system_prompt = self._load_prompt("narrative_agent.txt")

    def _load_prompt(self, filename: str) -> str:
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return DEFAULT_SYSTEM_PROMPT

    async def run(self, input_data: AnalyticsAgentOutput) -> NarrativeAgentOutput:
        insights = input_data.insights

        user_message = self._build_user_message(insights)

        response = await self.client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )

        raw = response.choices[0].message.content or "{}" if response.choices else "{}"
        script = self._parse_script(raw, insights.personality.value)

        self.log.info("narrative_agent.complete", scenes=len(script.scenes), title=script.title)

        return NarrativeAgentOutput(script=script)

    def _build_user_message(self, insights: object) -> str:  # type: ignore[type-arg]
        from backend.models.insights import FinancialInsights
        i: FinancialInsights = insights  # type: ignore[assignment]

        top_cats = ", ".join(
            f"{c.category} ({c.percentage:.0f}%)" for c in i.top_categories
        )
        achievements = "; ".join(i.achievements)

        return f"""
Financial Summary for {i.period_label}:
- Total Income: {i.currency} {i.total_income:,.2f}
- Total Expenses: {i.currency} {i.total_expenses:,.2f}
- Savings: {i.currency} {i.savings_amount:,.2f} ({i.savings_rate:.1f}% savings rate)
- Top Spending Categories: {top_cats}
- Key Achievements: {achievements}
- Financial Personality: {i.personality.value}
- Personality Reason: {i.personality_reason}

Generate a 5-scene cinematic video script as JSON following the scene structure in your system prompt.
""".strip()

    def _parse_script(self, raw_json: str, personality: str) -> NarrativeScript:
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            log.error("narrative_agent.json_parse_failed", raw=raw_json[:500])
            raise ValueError(f"Invalid JSON response from LLM: {raw_json[:200]}") from exc
        scenes = [
            Scene(
                id=s.get("id", i + 1),
                narration=s.get("narration", f"Scene {i + 1}."),
                visual_prompt=s.get("visual_prompt", f"Scene {i + 1} visual."),
            )
            for i, s in enumerate(data.get("scenes", []))
        ]
        if not scenes:
            raise ValueError(
                f"LLM returned 0 scenes — expected at least 1. Raw: {raw_json[:200]}"
            )
        return NarrativeScript(
            title=data.get("title", "Your Financial Recap"),
            personality=data.get("personality", personality),
            scenes=scenes,
        )


DEFAULT_SYSTEM_PROMPT = """
You are a warm, encouraging financial narrator producing scripts for personalized financial recap videos.

RULES:
- Write exactly 5 scenes using the cinematic 5-act structure:
  Scene 1 — Opening / Personality Reveal (open with the Financial Personality label)
  Scene 2 — Big Achievement (savings rate, debt payoff, or investment milestone)
  Scene 3 — Spending Insight (top category, positive framing)
  Scene 4 — Personalized Advice (one concrete, actionable tip for this personality)
  Scene 5 — Motivational Close (forward-looking, warm sign-off)
- Tone: upbeat, motivational, precise, warm
- Never fabricate numbers — use ONLY the data provided
- Keep each scene narration to 2-3 sentences (approx 15 seconds when spoken)
- Each visual_prompt should describe a clean, professional, abstract financial visualization

OUTPUT FORMAT (JSON only, no markdown):
{
  "title": "Your [Month] Financial Journey",
  "personality": "Financial Builder",
  "scenes": [
    {
      "id": 1,
      "narration": "...",
      "visual_prompt": "A minimalist illustration of ..."
    },
    ...
  ]
}
""".strip()
