"""
Backblaze B2 Storage Client.

Uses boto3 with the B2 S3-compatible API endpoint.
All pipeline artifacts are stored under:
  {user_id}/{session_id}/input/
  {user_id}/{session_id}/pipeline/
  {user_id}/{session_id}/output/
  {user_id}/{session_id}/metadata/
"""

from __future__ import annotations

import json
from pathlib import Path

import boto3
import structlog
from botocore.config import Config

log = structlog.get_logger()


class B2Client:
    """Backblaze B2 storage client (S3-compatible)."""

    def __init__(
        self,
        endpoint_url: str,
        key_id: str,
        application_key: str,
        bucket_name: str,
        presigned_url_expiry: int = 3600,
    ) -> None:
        self.bucket = bucket_name
        self.expiry = presigned_url_expiry
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=application_key,
            config=Config(signature_version="s3v4"),
        )

    # ── Upload helpers ────────────────────────────────────────────────────────

    def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        """Upload raw bytes to B2. Returns the B2 URI."""
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        log.info("b2.upload", key=key, bytes=len(data))
        return f"b2://{self.bucket}/{key}"

    def upload_file(self, key: str, local_path: Path, content_type: str) -> str:
        """Upload a local file to B2. Returns the B2 URI."""
        with open(local_path, "rb") as f:
            return self.upload_bytes(key, f.read(), content_type)

    def upload_json(self, key: str, data: dict) -> str:  # type: ignore[type-arg]
        """Upload a dict as JSON to B2."""
        payload = json.dumps(data, indent=2, default=str).encode("utf-8")
        return self.upload_bytes(key, payload, "application/json")

    # ── Download helpers ──────────────────────────────────────────────────────

    def download_bytes(self, key: str) -> bytes:
        """Download an object from B2 and return raw bytes."""
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        data: bytes = response["Body"].read()
        log.info("b2.download", key=key, bytes=len(data))
        return data

    # ── Key builders ──────────────────────────────────────────────────────────

    @staticmethod
    def input_key(user_id: str, session_id: str, filename: str) -> str:
        return f"{user_id}/{session_id}/input/{filename}"

    @staticmethod
    def pipeline_key(user_id: str, session_id: str, filename: str) -> str:
        return f"{user_id}/{session_id}/pipeline/{filename}"

    @staticmethod
    def scene_key(user_id: str, session_id: str, scene_id: int) -> str:
        return f"{user_id}/{session_id}/pipeline/scenes/scene_{scene_id:02d}.jpg"

    @staticmethod
    def output_key(user_id: str, session_id: str) -> str:
        return f"{user_id}/{session_id}/output/recap_{session_id}.mp4"

    @staticmethod
    def narration_key(user_id: str, session_id: str) -> str:
        return f"{user_id}/{session_id}/pipeline/narration.mp3"

    @staticmethod
    def metadata_key(user_id: str, session_id: str) -> str:
        return f"{user_id}/{session_id}/metadata/session_metadata.json"

    @staticmethod
    def analytics_key(user_id: str, session_id: str) -> str:
        return f"{user_id}/{session_id}/pipeline/analytics.json"

    @staticmethod
    def prompts_key(user_id: str, session_id: str) -> str:
        return f"{user_id}/{session_id}/pipeline/prompts.json"

    @staticmethod
    def generation_key(user_id: str, session_id: str) -> str:
        return f"{user_id}/{session_id}/pipeline/generation.json"

    @staticmethod
    def thumbnail_key(user_id: str, session_id: str) -> str:
        return f"{user_id}/{session_id}/pipeline/thumbnail.png"

    # ── Presigned URL ─────────────────────────────────────────────────────────

    def presigned_url(self, key: str) -> str:
        """Generate a presigned GET URL for a B2 object."""
        url: str = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.expiry,
        )
        return url
