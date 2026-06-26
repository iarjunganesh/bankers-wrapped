"""Unit tests for SessionStore — uses an in-memory SQLite DB."""

import pytest

from backend.storage.session_store import SessionStore


@pytest.fixture
def store(tmp_path):
    return SessionStore(db_path=tmp_path / "test.db")


def test_create_and_get(store):
    store.create("sess-1", "user-1")
    row = store.get("sess-1")
    assert row is not None
    assert row["session_id"] == "sess-1"
    assert row["user_id"] == "user-1"
    assert row["status"] == "pending"


def test_get_missing_returns_none(store):
    assert store.get("does-not-exist") is None


def test_set_processing(store):
    store.create("sess-2", "user-2")
    store.set_processing("sess-2")
    row = store.get("sess-2")
    assert row["status"] == "processing"


def test_set_complete(store):
    store.create("sess-3", "user-3")
    store.set_complete("sess-3", "https://b2.example.com/recap.mp4", {"model": "flux"})
    row = store.get("sess-3")
    assert row["status"] == "complete"
    assert row["output_url"] == "https://b2.example.com/recap.mp4"
    assert row["metadata"] == {"model": "flux"}


def test_set_failed(store):
    store.create("sess-4", "user-4")
    store.set_failed("sess-4", "pipeline exploded")
    row = store.get("sess-4")
    assert row["status"] == "failed"
    assert row["error"] == "pipeline exploded"


def test_set_failed_truncates_long_error(store):
    store.create("sess-5", "user-5")
    long_error = "x" * 2000
    store.set_failed("sess-5", long_error)
    row = store.get("sess-5")
    assert len(row["error"]) == 1000


def test_metadata_roundtrips_as_dict(store):
    store.create("sess-6", "user-6")
    store.set_complete("sess-6", "https://example.com", {"a": 1, "b": [2, 3]})
    row = store.get("sess-6")
    assert row["metadata"] == {"a": 1, "b": [2, 3]}


def test_append_event_stores_event(store):
    store.create("sess-7", "user-7")
    store.append_event("sess-7", "parsing", "Parsing transactions.csv")
    events = store.get_events("sess-7")
    assert len(events) == 1
    assert events[0]["event"] == "parsing"
    assert events[0]["detail"] == "Parsing transactions.csv"
    assert "ts" in events[0]


def test_append_multiple_events_in_order(store):
    store.create("sess-8", "user-8")
    store.append_event("sess-8", "parsing", "step 1")
    store.append_event("sess-8", "analyzing", "step 2")
    store.append_event("sess-8", "scripting", "step 3")
    events = store.get_events("sess-8")
    assert [e["event"] for e in events] == ["parsing", "analyzing", "scripting"]


def test_get_events_empty_for_new_session(store):
    store.create("sess-9", "user-9")
    assert store.get_events("sess-9") == []


def test_append_event_noop_for_missing_session(store):
    store.append_event("nonexistent", "parsing", "detail")
    assert store.get_events("nonexistent") == []
