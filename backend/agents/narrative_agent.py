"""
Narrative Agent.

Transforms FinancialInsights into a structured NarrativeScript (5 scenes).

Provider selection (ADR-007 / WS-1): script generation is SDK-only. The agent
always routes through Genblaze chat with a configured backend model.
NARRATIVE_PROVIDER selects which backend model id is used (e.g. NVIDIA NIM via
`nvidia-nim/...`), but no direct provider SDKs are invoked from this agent.
Invalid JSON is retried once; if the primary model is exhausted (call failure
or invalid JSON), one final attempt routes through NVIDIA NIM via the same SDK
before failing the run.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from backend.agents.analytics_agent import AnalyticsAgentOutput
from backend.agents.base import BaseAgent
from backend.config import Settings
from backend.media.genblaze_client import GenblazeClient
from backend.models.narrative import NarrativeScript, Scene

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
log = structlog.get_logger()


@dataclass
class NarrativeAgentOutput:
    script: NarrativeScript
    # LLM provenance for generation.json: label, model, provider, latency_ms,
    # retry_count (+ tokens/cost when the genblaze path produced the script).
    llm: dict = field(default_factory=dict)  # type: ignore[type-arg]


class NarrativeAgent(BaseAgent):
    """Generates a structured 5-scene video script from financial insights."""

    def __init__(self, settings: Settings, genblaze: GenblazeClient | None = None) -> None:
        super().__init__("NarrativeAgent")
        self.settings = settings
        if genblaze is None:
            raise ValueError("NarrativeAgent requires GenblazeClient (SDK-only narrative routing).")
        self.genblaze = genblaze
        self._sdk_model = self._select_sdk_model(settings)
        self.log.info(
            "narrative_agent.provider",
            provider="genblaze-sdk",
            model=self._sdk_model,
        )

        self._system_prompt = self._load_prompt("narrative_agent.txt")

    @staticmethod
    def _nim_model(settings: Settings) -> str:
        """NVIDIA NIM model id in SDK form (`nvidia-nim/` prefixed)."""
        if settings.nvidia_nim_model.startswith("nvidia-nim/"):
            return settings.nvidia_nim_model
        return f"nvidia-nim/{settings.nvidia_nim_model}"

    @staticmethod
    def _select_sdk_model(settings: Settings) -> str:
        """
        Resolve the SDK chat model from the narrative provider mode.

        - narrative_provider=genblaze  -> use settings.gmi_chat_model
        - narrative_provider=nvidia-nim -> force nvidia-nim/<model>
        """
        if settings.narrative_provider == "nvidia-nim":
            return NarrativeAgent._nim_model(settings)
        return settings.gmi_chat_model

    def _load_prompt(self, filename: str) -> str:
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return DEFAULT_SYSTEM_PROMPT

    async def run(self, input_data: AnalyticsAgentOutput) -> NarrativeAgentOutput:
        insights = input_data.insights
        user_message = self._build_user_message(insights)
        personality = insights.personality.value

        script, llm_info = await self._try_genblaze(user_message, personality)
        if script is None:
            raise RuntimeError("Narrative generation failed via Genblaze SDK after retries.")

        self.log.info(
            "narrative_agent.complete",
            scenes=len(script.scenes),
            title=script.title,
            provider=llm_info.get("provider"),
        )
        return NarrativeAgentOutput(script=script, llm=llm_info)

    async def _try_genblaze(
        self, user_message: str, personality: str
    ) -> tuple[NarrativeScript | None, dict]:  # type: ignore[type-arg]
        """
        Genblaze SDK chat path (ADR-007). Invalid/unschematic JSON is retried
        once; if the primary model is exhausted (call failure or invalid JSON),
        one final attempt routes through NVIDIA NIM via the same SDK. Any
        remaining failure returns (None, {}) so the caller can fail the run
        explicitly without invoking a non-SDK path.
        """
        nim_model = self._nim_model(self.settings)
        models = [self._sdk_model, self._sdk_model]
        if self._sdk_model != nim_model:
            models.append(nim_model)
        total_latency = 0
        total_retries = 0
        for attempt, model in enumerate(models):
            if model != self._sdk_model:
                self.log.warning("narrative_agent.fallback_to_nim", model=model)
            try:
                result = await self.genblaze.generate_script_text(
                    system=self._system_prompt,
                    user=user_message,
                    model=model,
                )
            except Exception as exc:
                self.log.warning(
                    "narrative_agent.genblaze_call_failed",
                    attempt=attempt,
                    error=str(exc),
                )
                continue
            total_latency += result.latency_ms
            total_retries += result.retry_count
            try:
                script = self._parse_script(result.text, personality)
            except ValueError:
                self.log.warning("narrative_agent.genblaze_invalid_json", attempt=attempt)
                continue  # one schema retry, then fall through to fallback
            return script, {
                "label": result.model
                if result.model.startswith(f"{result.provider}/")
                else f"{result.provider}/{result.model}",
                "provider": result.provider,
                "model": result.model,
                "latency_ms": total_latency,
                "retry_count": total_retries + attempt,
                "tokens_in": result.tokens_in,
                "tokens_out": result.tokens_out,
                "cost_usd": result.cost_usd,
            }
        self.log.error("narrative_agent.genblaze_exhausted")
        return None, {}

    def _build_user_message(self, insights: object) -> str:  # type: ignore[type-arg]
        from backend.models.insights import FinancialInsights

        i: FinancialInsights = insights  # type: ignore[assignment]

        top_cats = ", ".join(f"{c.category} ({c.percentage:.0f}%)" for c in i.top_categories)
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
            raise ValueError(f"LLM returned 0 scenes — expected at least 1. Raw: {raw_json[:200]}")
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
