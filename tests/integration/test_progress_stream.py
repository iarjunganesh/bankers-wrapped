"""Integration tests for the SSE progress endpoint."""

import json
import uuid

from backend.api.v1.recap import get_session_store


def _parse_sse(body: str) -> list[dict]:
    """Extract the JSON payloads from an SSE response body."""
    return [
        json.loads(line[len("data: "):])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


class TestProgressStream:
    def test_stream_replays_events_and_ends_with_complete(self, api_client):
        store = get_session_store()
        sid = str(uuid.uuid4())
        store.create(sid, "user-1")
        store.set_processing(sid)
        store.append_event(sid, "parsing", "Parsing jan.csv")
        store.append_event(sid, "analyzing", "Calculating insights")
        store.set_complete(sid, output_url="https://presigned.url/recap.mp4", metadata={})

        resp = api_client.get(f"/api/v1/recap/{sid}/progress")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        events = _parse_sse(resp.text)
        names = [e["event"] for e in events]
        assert names[:2] == ["parsing", "analyzing"]
        assert names[-1] == "complete"
        assert events[-1]["detail"] == "https://presigned.url/recap.mp4"
        # every event carries a real timestamp for per-step latency in the UI
        assert all(e["ts"] > 0 for e in events)

    def test_stream_ends_with_failed_for_failed_session(self, api_client):
        store = get_session_store()
        sid = str(uuid.uuid4())
        store.create(sid, "user-1")
        store.append_event(sid, "parsing", "Parsing")
        store.set_failed(sid, "boom")

        resp = api_client.get(f"/api/v1/recap/{sid}/progress")

        events = _parse_sse(resp.text)
        assert events[-1]["event"] == "failed"
