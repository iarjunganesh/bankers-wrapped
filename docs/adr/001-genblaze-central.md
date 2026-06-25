# ADR-001: Genblaze as Sole Media Generation Layer
**Status:** Accepted | **Date:** 2026-06-25

## Decision
All generative media calls route through the Genblaze SDK. No provider is called directly.

## Rationale
- Required by hackathon rules
- Single retry boundary for all media generation  
- Provider-agnostic: swap ElevenLabs to OpenAI TTS with one config flag
- SHA-256 provenance manifest on every run via genblaze-core
