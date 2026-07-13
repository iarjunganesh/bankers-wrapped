from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Banker's Wrapped"
    app_version: str = "1.9.1"
    debug: bool = False

    # CORS — defaults to wildcard for hackathon; override via CORS_ALLOW_ORIGINS env var in production
    cors_allow_origins: list[str] = ["*"]

    # OpenAI — TTS narration via GenblazeClient
    openai_api_key: str = ""
    openai_model: str = "openai/gpt-5.4-mini"  # fallback models_used.llm label only; real script model is resolved via Genblaze provenance
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "alloy"

    # GMI Cloud (via Genblaze) — image generation
    gmi_api_key: str = ""
    gmi_image_model: str = "seedream-4-0-250828"

    # Backblaze B2
    b2_key_id: str = ""
    b2_application_key: str = ""
    b2_endpoint_url: str = ""  # copy exact endpoint from B2 bucket details, e.g. https://s3.eu-central-003.backblazeb2.com
    b2_bucket_name: str = "bankers-wrapped-assets"
    b2_presigned_url_expiry: int = 3600

    # Pipeline
    pipeline_version: str = "1.0.0"
    pipeline_timeout_image: int = 300
    ffmpeg_scene_duration: int = 8  # seconds per scene image in final MP4
    ffmpeg_bin: str = "ffmpeg"  # override via FFMPEG_BIN env var if not on PATH

    # NVIDIA NIM — OpenAI-compatible LLM endpoint
    # If set, NarrativeAgent uses NIM instead of OpenAI. Leave blank to use OpenAI.
    nvidia_nim_api_key: str = ""
    nvidia_nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_nim_model: str = "meta/llama-3.1-70b-instruct"

    # Narrative LLM routing (ADR-007 / WS-1), SDK-only.
    # The narrative agent always calls Genblaze chat; narrative_provider selects
    # which backend model to request through that SDK path.
    #   - narrative_provider=genblaze   -> use gmi_chat_model
    #   - narrative_provider=nvidia-nim -> force nvidia-nim/<nvidia_nim_model>
    narrative_provider: str = "genblaze"  # "genblaze" | "nvidia-nim"
    # Default points at NIM's free dev tier to preserve GMI credits locally; prod
    # overrides via GMI_CHAT_MODEL=openai/gpt-5.4-mini (see .env.example / ADR-007).
    gmi_chat_model: str = "nvidia-nim/meta/llama-3.1-70b-instruct"

    # Plaid — optional "connect a bank (sandbox)" ingestion path (ADR-010).
    # Leave blank to disable; the CSV upload path is unaffected.
    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"

    @property
    def plaid_enabled(self) -> bool:
        return bool(self.plaid_client_id and self.plaid_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
