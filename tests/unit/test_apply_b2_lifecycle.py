"""Unit tests for scripts/apply_b2_lifecycle.py (ADR-009)."""

from unittest.mock import MagicMock

from scripts.apply_b2_lifecycle import apply_lifecycle, load_lifecycle_config


class TestB2Lifecycle:
    def test_load_strips_comment_and_keeps_rules(self):
        config = load_lifecycle_config()
        assert set(config.keys()) == {"Rules"}
        assert len(config["Rules"]) == 1
        rule = config["Rules"][0]
        assert rule["Status"] == "Enabled"
        # Retention must outlast the judging period (ends Aug 11, 2026) for any
        # session created during the hackathon window.
        assert rule["Expiration"]["Days"] >= 45

    def test_apply_b2_lifecycle_builds_expected_payload(self):
        client = MagicMock()
        client.get_bucket_lifecycle_configuration.return_value = {
            "Rules": [{"ID": "expire-recap-sessions-45d"}]
        }
        config = load_lifecycle_config()

        result = apply_lifecycle(client, "test-bucket", config)

        client.put_bucket_lifecycle_configuration.assert_called_once_with(
            Bucket="test-bucket",
            LifecycleConfiguration=config,
        )
        assert result["Rules"][0]["ID"] == "expire-recap-sessions-45d"
