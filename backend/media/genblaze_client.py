"""
Genblaze SDK client wrapper.

Routes all generative media calls through the Genblaze Pipeline API.
No AI provider is called directly — every request goes through genblaze-core.

Providers used:
  - genblaze-gmicloud  → GMI Cloud Seedream image generation
  - genblaze-s3        → Backblaze B2 storage sink
  - openai (TTS)       → Narration audio synthesis (wrapped here; no direct calls elsewhere)

Retry policy: up to 3 attempts with exponential backoff (2s, 4s) for both
image generation and audio synthesis. Retry count and wall-clock latency
are returned in each result for provenance tracking.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field

import httpx
import openai
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = structlog.get_logger()



@dataclass
class ImageResult:
    image_bytes: bytes
    manifest_hash: str
    latency_ms: int = field(default=0)
    retry_count: int = field(default=0)


@dataclass
class AudioResult:
    audio_bytes: bytes
    model: str
    voice: str
    latency_ms: int = field(default=0)
    retry_count: int = field(default=0)


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
        Generate a scene image via Genblaze → GMI Cloud (Seedream).

        Retries up to 3 times with exponential backoff. Returns ImageResult
        with raw PNG bytes, provenance manifest hash, wall-clock latency, and
        retry count for generation.json provenance.
        """
        attempt_count = 0

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _sync_generate() -> tuple[bytes, str]:
            """Blocking genblaze pipeline run + image fetch (runs off the loop)."""
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
            return image_bytes, pr.manifest.canonical_hash

        async def _attempt() -> ImageResult:
            nonlocal attempt_count
            t0 = int(time.time() * 1000)
            try:
                # Offload the SYNCHRONOUS genblaze run + HTTP fetch to a worker
                # thread so it doesn't block the event loop. This lets concurrent
                # image generations (via asyncio.gather) actually run in parallel
                # and keeps the SSE progress stream live during generation.
                image_bytes, manifest_hash = await asyncio.to_thread(_sync_generate)

                latency = int(time.time() * 1000) - t0
                log.info(
                    "genblaze.image.generate",
                    provider="gmi-cloud",
                    model=model,
                    bytes=len(image_bytes),
                    latency_ms=latency,
                    attempt=attempt_count,
                )
                return ImageResult(
                    image_bytes=image_bytes,
                    manifest_hash=manifest_hash,
                    latency_ms=latency,
                    retry_count=attempt_count,
                )
            except Exception:
                attempt_count += 1
                raise

        return await _attempt()

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
        Retries up to 3 times with exponential backoff.
        """
        attempt_count = 0

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        async def _attempt() -> AudioResult:
            nonlocal attempt_count
            t0 = int(time.time() * 1000)
            try:
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
                latency = int(time.time() * 1000) - t0
                log.info(
                    "genblaze.audio.generate",
                    model=model,
                    voice=voice,
                    bytes=len(audio_bytes),
                    latency_ms=latency,
                    attempt=attempt_count,
                )
                return AudioResult(
                    audio_bytes=audio_bytes,
                    model=model,
                    voice=voice,
                    latency_ms=latency,
                    retry_count=attempt_count,
                )
            except Exception:
                attempt_count += 1
                raise

        return await _attempt()
