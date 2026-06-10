from datetime import date

from backend.app.core.schemas import EventCreate
from backend.app.services.pipeline import MemoryPipeline
from backend.app.services.reflection import ReflectionEngine
from backend.app.services.store import MemoryStore


def test_memory_pipeline_round_trip(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store)

    event = pipeline.ingest_event(
        EventCreate(
            text="今天决定 Open Memory 先做 FastAPI 和 SQLite MVP，再接 Whisper 和 iPhone VAD。",
            source="test",
        )
    )

    assert event["category"] in {"project", "decision"}
    assert event["importance"] >= 0.5

    summary = pipeline.summarize_day(date.today())
    assert "Open Memory" in summary["summary"]

    reflection = ReflectionEngine(store).reflect_on_day(date.today())
    assert "Reflection" in reflection["text"]

    answer, events, memories = pipeline.query("Open Memory MVP")
    assert "Open Memory" in answer
    assert events
    assert memories


def test_memory_inbox_review_and_promotion(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store)

    event = pipeline.ingest_event(
        EventCreate(
            text="Open Memory v1 要先做 Memory Inbox，让用户决定哪些内容进入长期记忆。",
            source="test",
        )
    )

    assert event["review_status"] == "inbox"
    assert store.list_inbox_events()

    reviewed = store.update_event_review(event["id"], review_status="ignored")
    assert reviewed["review_status"] == "ignored"
    assert not store.recent_events()

    kept = store.update_event_review(event["id"], review_status="kept", importance=0.9)
    assert kept["current_importance"] == 0.9

    memory = pipeline.promote_event(event["id"])
    assert memory["text"] == kept["text"]
    assert memory["confidence"] == 0.9
