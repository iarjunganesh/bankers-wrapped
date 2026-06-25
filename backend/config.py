from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Banker's Wrapped"
    app_version: str = "1.0.0"
    debug: bool = False

    # CORS — set to specific origins in production (e.g. https://bankers-wrapped.vercel.app)
    cors_allow_origins: list[str] = ["*"]

    # OpenAI — used only as LLM fallback in NarrativeAgent when NIM key is absent
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # GMI Cloud (via Genblaze) — image generation
    gmi_api_key: str = ""
    gmi_image_model: str = "Flux2-Dev"

    # ElevenLabs (via Genblaze) — voice narration
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    elevenlabs_model: str = "eleven_multilingual_v2"

    # Backblaze B2
    b2_key_id: str = ""
    b2_application_key: str = ""
    b2_endpoint_url: str = ""  # copy exact endpoint from B2 bucket details, e.g. https://s3.eu-central-003.backblazeb2.com
    b2_bucket_name: str = "bankers-wrapped-assets"
    b2_presigned_url_expiry: int = 3600

    # Pipeline
    pipeline_version: str = "1.0.0"
    pipeline_timeout_image: int = 120
    pipeline_timeout_audio: int = 90
    ffmpeg_scene_duration: int = 8  # seconds per scene image in final MP4

    # NVIDIA NIM — OpenAI-compatible LLM endpoint
    # If set, NarrativeAgent uses NIM instead of OpenAI. Leave blank to use OpenAI.
    nvidia_nim_api_key: str = ""
    nvidia_nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_nim_model: str = "meta/llama-3.1-70b-instruct"


@lru_cache
def get_settings() -> Settings:
    return Settings()
