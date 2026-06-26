"""Unit tests for B2Client — mocks boto3."""

import json
from unittest.mock import patch

import pytest

from backend.storage.b2_client import B2Client


@pytest.fixture
def mock_boto3():
    with patch("backend.storage.b2_client.boto3") as mock:
        yield mock


@pytest.fixture
def b2(mock_boto3) -> B2Client:
    return B2Client(
        endpoint_url="https://s3.us-west-004.backblazeb2.com",
        key_id="test-key-id",
        application_key="test-app-key",
        bucket_name="test-bucket",
        presigned_url_expiry=3600,
    )


class TestB2Client:
    def test_upload_bytes_calls_put_object(self, b2, mock_boto3):
        b2.upload_bytes("some/key.csv", b"data", "text/csv")
        b2._client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="some/key.csv",
            Body=b"data",
            ContentType="text/csv",
        )

    def test_upload_bytes_returns_b2_uri(self, b2, mock_boto3):
        result = b2.upload_bytes("some/key.mp4", b"video", "video/mp4")
        assert result == "b2://test-bucket/some/key.mp4"

    def test_upload_json_serialises_dict(self, b2, mock_boto3):
        data = {"session_id": "abc", "status": "complete"}
        b2.upload_json("meta/key.json", data)
        call_args = b2._client.put_object.call_args
        body = call_args.kwargs["Body"]
        parsed = json.loads(body)
        assert parsed["session_id"] == "abc"

    def test_presigned_url_called(self, b2, mock_boto3):
        b2._client.generate_presigned_url.return_value = "https://presigned.url/key"
        url = b2.presigned_url("output/recap.mp4")
        assert url == "https://presigned.url/key"
        b2._client.generate_presigned_url.assert_called_once()

    def test_input_key_format(self):
        key = B2Client.input_key("user1", "sess1", "transactions.csv")
        assert key == "user1/sess1/input/transactions.csv"

    def test_pipeline_key_format(self):
        key = B2Client.pipeline_key("user1", "sess1", "script.json")
        assert key == "user1/sess1/pipeline/script.json"

    def test_scene_key_format(self):
        key = B2Client.scene_key("user1", "sess1", 3)
        assert key == "user1/sess1/pipeline/scenes/scene_03.png"

    def test_output_key_format(self):
        key = B2Client.output_key("user1", "sess1")
        assert key == "user1/sess1/output/recap_sess1.mp4"

    def test_narration_key_format(self):
        key = B2Client.narration_key("user1", "sess1")
        assert key == "user1/sess1/pipeline/narration.mp3"

    def test_metadata_key_format(self):
        key = B2Client.metadata_key("user1", "sess1")
        assert key == "user1/sess1/metadata/session_metadata.json"

    def test_upload_file_reads_and_uploads(self, b2, mock_boto3, tmp_path):
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"audio data")
        result = b2.upload_file("audio/narration.mp3", test_file, "audio/mpeg")
        assert result.startswith("b2://")
