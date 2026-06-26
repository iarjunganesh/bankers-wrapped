"""
Media Agent.

Consolidated agent responsible for:
  1. genblaze.image.generate()        → GMI Cloud Seedream scene images (PNG × N, parallel)
  2. genblaze.generate_narration_audio() → OpenAI TTS narration MP3 (via GenblazeClient)
  3. FFmpeg composition               → images + audio → recap.mp4
  4. Backblaze B2 upload              → all assets stored, presigned URL returned

All generative media calls route through the Genblaze SDK (GenblazeClient wrapper).
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import structlog

from backend.agents.base import BaseAgent
from backend.agents.narrative_agent import NarrativeAgentOutput
from backend.config import Settings
from backend.media.ffmpeg_composer import FFmpegComposer
from backend.media.genblaze_client import GenblazeClient
from backend.models.session import PipelineMetadata
from backend.storage.b2_client import B2Client

log = structlog.get_logger()


@dataclass
class MediaAgentInput:
    script_output: NarrativeAgentOutput
    session_id: str
    user_id: str
    csv_bytes: bytes
    input_hash: str
    input_filename: str


@dataclass
class MediaAgentOutput:
    video_url: str
    metadata: PipelineMetadata
    b2_keys: dict[str, str]


class MediaAgent(BaseAgent):
    """
    Orchestrates voice synthesis, image generation, FFmpeg composition,
    and Backblaze B2 storage for the full media pipeline.
    """

    def __init__(
        self,
        settings: Settings,
        genblaze: GenblazeClient,
        b2: B2Client,
    ) -> None:
        super().__init__("MediaAgent")
        self.settings = settings
        self.genblaze = genblaze
        self.b2 = b2
        self.composer = FFmpegComposer(
            scene_duration_seconds=settings.ffmpeg_scene_duration
        )

    async def run(self, input_data: MediaAgentInput) -> MediaAgentOutput:
        start_ms = int(time.time() * 1000)
        script = input_data.script_output.script
        session_id = input_data.session_id
        user_id = input_data.user_id

        b2_keys: dict[str, str] = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # ── 1. Upload raw CSV to B2 input/ ──────────────────────────────
            csv_key = B2Client.input_key(user_id, session_id, input_data.input_filename)
            self.b2.upload_bytes(csv_key, input_data.csv_bytes, "text/csv")
            b2_keys["csv"] = csv_key

            # ── 2. Upload narrative script to B2 pipeline/ ──────────────────
            script_key = B2Client.pipeline_key(user_id, session_id, "script.json")
            self.b2.upload_json(script_key, script.model_dump())
            b2_keys["script"] = script_key

            # ── 3. Generate scene images in parallel via Genblaze → GMI Cloud ──
            async def _gen_image(idx: int, prompt: str):
                self.log.info("media_agent.image.start", scene_idx=idx)
                return await self.genblaze.generate_scene_image(
                    prompt=prompt,
                    model=self.settings.gmi_image_model,
                    timeout=self.settings.pipeline_timeout_image,
                )

            image_results = await asyncio.gather(*[
                _gen_image(i, scene.visual_prompt)
                for i, scene in enumerate(script.scenes)
            ])

            scene_image_paths: list[Path] = []
            image_manifest_hashes: list[str] = []
            for idx, image_result in enumerate(image_results):
                img_path = tmp / f"scene_{idx:02d}.png"
                img_path.write_bytes(image_result.image_bytes)
                scene_image_paths.append(img_path)
                image_manifest_hashes.append(image_result.manifest_hash)

                scene_key = B2Client.scene_key(user_id, session_id, idx)
                self.b2.upload_bytes(scene_key, image_result.image_bytes, "image/png")
                b2_keys[f"scene_{idx}"] = scene_key

            # ── 4. Synthesise narration audio via Genblaze (OpenAI TTS) ────────
            full_narration = " ".join(scene.narration for scene in script.scenes)
            self.log.info("media_agent.narration.start")
            audio_result = await self.genblaze.generate_narration_audio(
                narration_text=full_narration,
                model=self.settings.openai_tts_model,
                voice=self.settings.openai_tts_voice,
            )
            narration_path = tmp / "narration.mp3"
            narration_path.write_bytes(audio_result.audio_bytes)

            narration_key = B2Client.narration_key(user_id, session_id)
            self.b2.upload_bytes(narration_key, audio_result.audio_bytes, "audio/mpeg")
            b2_keys["narration"] = narration_key

            # ── 5. Compose final MP4 with FFmpeg (images + narration audio) ──
            self.log.info("media_agent.compose.start")
            output_path = tmp / f"recap_{session_id}.mp4"
            await self.composer.compose(
                scene_image_paths=scene_image_paths,
                output_path=output_path,
                audio_path=narration_path,
                title=script.title,
                personality=script.personality,
            )

            # ── 6. Upload final MP4 to B2 output/ ──────────────────────────
            video_key = B2Client.output_key(user_id, session_id)
            video_bytes = output_path.read_bytes()
            self.b2.upload_bytes(video_key, video_bytes, "video/mp4")
            b2_keys["video"] = video_key

            video_url = self.b2.presigned_url(video_key)

            # ── 7. Build and upload provenance metadata ──────────────────────
            elapsed_ms = int(time.time() * 1000) - start_ms
            metadata = PipelineMetadata(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(UTC),
                pipeline_version=self.settings.pipeline_version,
                models_used={
                    "llm": (
                        f"nvidia-nim/{self.settings.nvidia_nim_model}"
                        if self.settings.nvidia_nim_api_key
                        else self.settings.openai_model
                    ),
                    "image": f"gmi-cloud/{self.settings.gmi_image_model}",
                    "audio": f"openai/{audio_result.model}",
                    "compositor": "ffmpeg",
                },
                input_filename=input_data.input_filename,
                input_hash=input_data.input_hash,
                output_url=video_url,
                processing_time_ms=elapsed_ms,
                synthetic_data=False,
            )

            meta_key = B2Client.metadata_key(user_id, session_id)
            self.b2.upload_json(meta_key, json.loads(metadata.model_dump_json()))
            b2_keys["metadata"] = meta_key

            self.log.info(
                "media_agent.complete",
                session_id=session_id,
                elapsed_ms=elapsed_ms,
                video_key=video_key,
            )

            return MediaAgentOutput(
                video_url=video_url,
                metadata=metadata,
                b2_keys=b2_keys,
            )
