# ADR-001: Genblaze as Sole Media Generation Layer

**Status:** Accepted | **Date:** 2026-06-25

## Decision

All generative media calls route through the Genblaze SDK. No provider is called directly outside `backend/media/genblaze_client.py`.

Two provider types in use:

- **Images**: `GenblazeClient.generate_scene_image()` → GMI Cloud Seedream (`seedream-4-0-250828`)
- **Audio**: `GenblazeClient.generate_narration_audio()` → OpenAI TTS (`tts-1`, alloy voice)

## Rationale

- Required by hackathon rules — judges score on Genblaze usage
- Single abstraction boundary for all media generation; provider swaps require only config changes
- SHA-256 provenance manifest on every image run via `genblaze-core`
- OpenAI TTS wrapped inside GenblazeClient satisfies the "two provider types" scoring criterion
