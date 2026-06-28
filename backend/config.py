from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Banker's Wrapped"
    app_version: str = "1.5.0"
    debug: bool = False

    # CORS — defaults to wildcard for hackathon; override via CORS_ALLOW_ORIGINS env var in production
    cors_allow_origins: list[str] = ["*"]

    # OpenAI — LLM fallback in NarrativeAgent + TTS narration via GenblazeClient
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
