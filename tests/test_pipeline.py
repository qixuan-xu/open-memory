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
            text="今天决定 Allen Memory OS 先做 FastAPI 和 SQLite MVP，再接 Whisper 和 iPhone VAD。",
            source="test",
        )
    )

    assert event["category"] in {"project", "decision"}
    assert event["importance"] >= 0.5

    summary = pipeline.summarize_day(date.today())
    assert "Allen Memory OS" in summary["summary"]

    reflection = ReflectionEngine(store).reflect_on_day(date.today())
    assert "Reflection" in reflection["text"]

    answer, events, memories = pipeline.query("Allen Memory OS MVP")
    assert "Allen Memory OS" in answer
    assert events
    assert memories

