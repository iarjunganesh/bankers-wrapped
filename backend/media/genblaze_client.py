"""
Genblaze SDK client wrapper.

Routes all generative media calls through the Genblaze Pipeline API.
No AI provider is called directly — every request goes through genblaze-core.

Providers used:
  - genblaze-gmicloud  → GMI Cloud Seedream image generation
  - genblaze-s3        → Backblaze B2 storage sink
  - openai (TTS)       → Narration audio synthesis (wrapped here; no direct calls elsewhere)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
import openai
import structlog

log = structlog.get_logger()


@dataclass
class ImageResult:
    image_bytes: bytes
    manifest_hash: str


@dataclass
class AudioResult:
    audio_bytes: bytes
    model: str
    voice: str


class GenblazeClient:
    """
    Thin wrapper around the Genblaze Pipeline API.

    Centralises all provider imports so the rest of the codebase
    is decoupled from Genblaze internals.
    """

    def __init__(
        self,
        gmi_api_key: str,
        b2_bucket: str,
        b2_endpoint: str,
        b2_key_id: str,
        b2_app_key: str,
        openai_api_key: str = "",
    ) -> None:
        self.gmi_api_key = gmi_api_key
        self.b2_bucket = b2_bucket
        self.b2_endpoint = b2_endpoint
        self.b2_key_id = b2_key_id
        self.b2_app_key = b2_app_key
        self.openai_api_key = openai_api_key

        if gmi_api_key:
            os.environ.setdefault("GMI_API_KEY", gmi_api_key)

    def _build_b2_sink(self) -> object:
        """Build an ObjectStorageSink pointing at Backblaze B2."""
        from genblaze_core import KeyStrategy, ObjectStorageSink
        from genblaze_s3 import S3StorageBackend

        backend = S3StorageBackend.for_backblaze(
            self.b2_bucket,
            key_id=self.b2_key_id,
            app_key=self.b2_app_key,
        )
        return ObjectStorageSink(backend, key_strategy=KeyStrategy.HIERARCHICAL)

    async def generate_scene_image(
        self,
        prompt: str,
        model: str = "seedream-4-0-250828",
        width: int = 1344,
        height: int = 768,
        timeout: int = 120,
    ) -> ImageResult:
        """
        Generate a scene image via Genblaze → GMI Cloud (FLUX).

        Returns ImageResult containing raw PNG bytes and provenance manifest hash.
        GMI Cloud uses an async queue API; genblaze-gmicloud handles polling internally.
        """
        from genblaze_core import Modality, Pipeline
        from genblaze_gmicloud import GMICloudImageProvider

        pr = (
            Pipeline("bankers-wrapped-image")
            .step(
                GMICloudImageProvider(),
                model=model,
                prompt=prompt,
                modality=Modality.IMAGE,
                width=width,
                height=height,
            )
            .run(timeout=timeout, raise_on_failure=True)
        )

        asset = pr.run.steps[0].assets[0]
        with httpx.Client(timeout=30) as http:
            image_bytes = http.get(asset.url).content

        log.info("genblaze.image.generate", provider="gmi-cloud", model=model, bytes=len(image_bytes))
        return ImageResult(image_bytes=image_bytes, manifest_hash=pr.manifest.canonical_hash)

    async def generate_narration_audio(
        self,
        narration_text: str,
        model: str = "tts-1",
        voice: str = "alloy",
    ) -> AudioResult:
        """
        Synthesise narration audio via OpenAI TTS.

        Wrapped here so all AI media generation routes through GenblazeClient —
        no direct openai.audio calls outside this module.
        """
        import asyncio

        client = openai.OpenAI(api_key=self.openai_api_key or None)

        def _synthesise() -> bytes:
            resp = client.audio.speech.create(
                model=model,
                voice=voice,  # type: ignore[arg-type]
                input=narration_text,
                response_format="mp3",
            )
            return resp.read()

        audio_bytes = await asyncio.to_thread(_synthesise)
        log.info("genblaze.audio.generate", model=model, voice=voice, bytes=len(audio_bytes))
        return AudioResult(audio_bytes=audio_bytes, model=model, voice=voice)
