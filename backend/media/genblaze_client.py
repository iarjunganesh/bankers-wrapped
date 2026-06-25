"""
Genblaze SDK client wrapper.

Routes all generative media calls through the Genblaze Pipeline API.
No AI provider is called directly — every request goes through genblaze-core.

Providers used:
  - genblaze-gmicloud    → GMI Cloud FLUX image generation (Flux2-Dev)
  - genblaze-elevenlabs  → ElevenLabs TTS voice narration
  - genblaze-s3          → Backblaze B2 storage sink
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import structlog

log = structlog.get_logger()


@dataclass
class AudioResult:
    audio_bytes: bytes
    manifest_hash: str


@dataclass
class ImageResult:
    image_bytes: bytes
    manifest_hash: str


class GenblazeClient:
    """
    Thin wrapper around the Genblaze Pipeline API.

    Centralises all provider imports so the rest of the codebase
    is decoupled from Genblaze internals.
    """

    def __init__(
        self,
        gmi_api_key: str,
        elevenlabs_api_key: str,
        b2_bucket: str,
        b2_endpoint: str,
        b2_key_id: str,
        b2_app_key: str,
    ) -> None:
        self.gmi_api_key = gmi_api_key
        self.elevenlabs_api_key = elevenlabs_api_key
        self.b2_bucket = b2_bucket
        self.b2_endpoint = b2_endpoint
        self.b2_key_id = b2_key_id
        self.b2_app_key = b2_app_key

        # Set env vars that Genblaze providers read from the environment
        if gmi_api_key:
            os.environ.setdefault("GMI_API_KEY", gmi_api_key)
        if elevenlabs_api_key:
            os.environ.setdefault("ELEVENLABS_API_KEY", elevenlabs_api_key)

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

    async def synthesize_narration(
        self,
        script: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
        model: str = "eleven_multilingual_v2",
        timeout: int = 90,
    ) -> AudioResult:
        """
        Generate MP3 narration audio via Genblaze → ElevenLabs.

        Returns AudioResult containing raw audio bytes and provenance manifest hash.
        """
        from genblaze_core import Modality, Pipeline
        from genblaze_elevenlabs import ElevenLabsProvider

        with tempfile.TemporaryDirectory() as tmpdir:
            run, manifest = (
                Pipeline("bankers-wrapped-tts")
                .step(
                    ElevenLabsProvider(output_dir=tmpdir),
                    model=model,
                    prompt=script,
                    modality=Modality.AUDIO,
                    voice_id=voice_id,
                    response_format="mp3",
                )
                .run(timeout=timeout)
            )
            asset = run.steps[0].assets[0]
            audio_bytes = Path(asset.path).read_bytes()

        log.info("genblaze.audio.synthesize", provider="elevenlabs", bytes=len(audio_bytes))
        return AudioResult(audio_bytes=audio_bytes, manifest_hash=manifest.canonical_hash)

    async def generate_scene_image(
        self,
        prompt: str,
        model: str = "Flux2-Dev",
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

        with tempfile.TemporaryDirectory() as tmpdir:
            run, manifest = (
                Pipeline("bankers-wrapped-image")
                .step(
                    GMICloudImageProvider(output_dir=tmpdir),
                    model=model,
                    prompt=prompt,
                    modality=Modality.IMAGE,
                    width=width,
                    height=height,
                )
                .run(timeout=timeout)
            )
            asset = run.steps[0].assets[0]
            image_bytes = Path(asset.path).read_bytes()

        log.info("genblaze.image.generate", provider="gmi-cloud", model=model, bytes=len(image_bytes))
        return ImageResult(image_bytes=image_bytes, manifest_hash=manifest.canonical_hash)
