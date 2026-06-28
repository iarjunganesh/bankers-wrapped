"""
Media Agent.

Consolidated agent responsible for:
  1. genblaze.image.generate()        → GMI Cloud Seedream scene images (PNG × N, parallel)
  2. genblaze.generate_narration_audio() → OpenAI TTS narration MP3 (via GenblazeClient)
  3. FFmpeg composition               → images + audio → recap.mp4
  4. Backblaze B2 upload              → all assets stored, presigned URL returned

Full asset manifest uploaded to B2:
  analytics.json   — financial insights for this session
  prompts.json     — all image + narration prompts with hashes
  generation.json  — model, provider, latency, retry count per step
  thumbnail.png    — scene 0 image used as the recap preview thumbnail
  session_metadata.json — top-level provenance record
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import structlog

from backend.agents.analytics_agent import AnalyticsAgentOutput
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
    analytics_output: AnalyticsAgentOutput | None = None


@dataclass
class MediaAgentOutput:
    video_url: str
    thumbnail_url: str
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
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__("MediaAgent")
        self.settings = settings
        self.genblaze = genblaze
        self.b2 = b2
        self.progress_callback = progress_callback
        self.composer = FFmpegComposer(
            scene_duration_seconds=settings.ffmpeg_scene_duration,
            ffmpeg_bin=settings.ffmpeg_bin,
        )

    def _emit(self, event: str, detail: str) -> None:
        if self.progress_callback:
            self.progress_callback(event, detail)

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

            # ── 3. Upload analytics snapshot to B2 pipeline/ ────────────────
            if input_data.analytics_output is not None:
                analytics_key = B2Client.analytics_key(user_id, session_id)
                analytics_dict = json.loads(
                    input_data.analytics_output.insights.model_dump_json()
                )
                self.b2.upload_json(analytics_key, analytics_dict)
                b2_keys["analytics"] = analytics_key

            # ── 4. Generate scene images in parallel via Genblaze → GMI Cloud ─
            async def _gen_image(idx: int, prompt: str):
                self.log.info("media_agent.image.start", scene_idx=idx)
                result = await self.genblaze.generate_scene_image(
                    prompt=prompt,
                    model=self.settings.gmi_image_model,
                    timeout=self.settings.pipeline_timeout_image,
                )
                self._emit(f"scene_{idx}_done", f"Scene {idx + 1} generated")
                return result

            image_results = await asyncio.gather(*[
                _gen_image(i, scene.visual_prompt)
                for i, scene in enumerate(script.scenes)
            ])

            scene_image_paths: list[Path] = []
            for idx, image_result in enumerate(image_results):
                img_path = tmp / f"scene_{idx:02d}.jpg"
                img_path.write_bytes(image_result.image_bytes)
                scene_image_paths.append(img_path)

                scene_key = B2Client.scene_key(user_id, session_id, idx)
                self.b2.upload_bytes(scene_key, image_result.image_bytes, "image/jpeg")
                b2_keys[f"scene_{idx}"] = scene_key

            # ── 5. Upload thumbnail (scene 0) to B2 pipeline/ ──────────────
            thumbnail_key = B2Client.thumbnail_key(user_id, session_id)
            self.b2.upload_bytes(
                thumbnail_key, image_results[0].image_bytes, "image/jpeg"
            )
            b2_keys["thumbnail"] = thumbnail_key
            thumbnail_url = self.b2.presigned_url(thumbnail_key)

            # ── 6. Upload prompts manifest to B2 pipeline/ ──────────────────
            full_narration = " ".join(scene.narration for scene in script.scenes)
            prompts_payload = {
                "session_id": session_id,
                "generated_at": datetime.now(UTC).isoformat(),
                "scenes": [
                    {
                        "scene_idx": i,
                        "prompt": scene.visual_prompt,
                        "negative_prompt": "",
                        "seed": None,
                        "provider": "gmi-cloud",
                        "model": self.settings.gmi_image_model,
                        "prompt_hash": hashlib.sha256(
                            scene.visual_prompt.encode()
                        ).hexdigest()[:16],
                    }
                    for i, scene in enumerate(script.scenes)
                ],
                "narration_text_hash": hashlib.sha256(
                    full_narration.encode()
                ).hexdigest()[:16],
            }
            prompts_key = B2Client.prompts_key(user_id, session_id)
            self.b2.upload_json(prompts_key, prompts_payload)
            b2_keys["prompts"] = prompts_key

            # ── 7. Synthesise narration audio via Genblaze (OpenAI TTS) ────
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

            # ── 8. Compose final MP4 with FFmpeg (images + narration audio) ─
            self._emit("composing_video", "Composing final video with FFmpeg")
            self.log.info("media_agent.compose.start")
            compose_t0 = int(time.time() * 1000)
            output_path = tmp / f"recap_{session_id}.mp4"
            await self.composer.compose(
                scene_image_paths=scene_image_paths,
                output_path=output_path,
                audio_path=narration_path,
                title=script.title,
                personality=script.personality,
            )
            compose_latency_ms = int(time.time() * 1000) - compose_t0

            # ── 9. Upload final MP4 to B2 output/ ──────────────────────────
            self._emit("uploading_to_b2", "Uploading artifacts to Backblaze B2")
            video_key = B2Client.output_key(user_id, session_id)
            video_bytes = output_path.read_bytes()
            self.b2.upload_bytes(video_key, video_bytes, "video/mp4")
            b2_keys["video"] = video_key

            video_url = self.b2.presigned_url(video_key)

            # ── 10. Build and upload provenance metadata ─────────────────────
            elapsed_ms = int(time.time() * 1000) - start_ms
            llm_label = (
                f"nvidia-nim/{self.settings.nvidia_nim_model}"
                if self.settings.nvidia_nim_api_key
                else self.settings.openai_model
            )
            metadata = PipelineMetadata(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(UTC),
                pipeline_version=self.settings.pipeline_version,
                models_used={
                    "llm": llm_label,
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

            # ── 11. Upload generation provenance to B2 pipeline/ ────────────
            generation_payload = {
                "session_id": session_id,
                "generated_at": metadata.created_at.isoformat(),
                "pipeline_version": self.settings.pipeline_version,
                "images": [
                    {
                        "scene_idx": i,
                        "model": self.settings.gmi_image_model,
                        "provider": "gmi-cloud",
                        "prompt_hash": hashlib.sha256(
                            scene.visual_prompt.encode()
                        ).hexdigest()[:16],
                        "latency_ms": image_results[i].latency_ms,
                        "retry_count": image_results[i].retry_count,
                        "manifest_hash": image_results[i].manifest_hash,
                        "success": True,
                    }
                    for i, scene in enumerate(script.scenes)
                ],
                "audio": {
                    "model": audio_result.model,
                    "voice": audio_result.voice,
                    "provider": "openai",
                    "latency_ms": audio_result.latency_ms,
                    "retry_count": audio_result.retry_count,
                    "success": True,
                },
                "compositor": {
                    "tool": "ffmpeg",
                    "scenes": len(script.scenes),
                    "latency_ms": compose_latency_ms,
                    "success": True,
                },
                "total_latency_ms": elapsed_ms,
            }
            gen_key = B2Client.generation_key(user_id, session_id)
            self.b2.upload_json(gen_key, generation_payload)
            b2_keys["generation"] = gen_key

            self.log.info(
                "media_agent.complete",
                session_id=session_id,
                elapsed_ms=elapsed_ms,
                video_key=video_key,
                artifacts=len(b2_keys),
            )

            return MediaAgentOutput(
                video_url=video_url,
                thumbnail_url=thumbnail_url,
                metadata=metadata,
                b2_keys=b2_keys,
            )
