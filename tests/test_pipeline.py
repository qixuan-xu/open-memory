from datetime import date, datetime, timezone

from backend.app.core.schemas import EventCreate
from backend.app.services.answering import build_prompt
from backend.app.services.ingest_assessment import assess_event, build_ingest_prompt, parse_llm_assessment
from backend.app.services.pipeline import MemoryPipeline
from backend.app.services.reflection import ReflectionEngine
from backend.app.services.store import MemoryStore
from open_memory.llms import LLMConfig, LLMError, create_llm_client, extract_chat_text, extract_openai_text, post_json


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
    assert event["importance_reason"]
    assert "captured_at" in event["metadata"]
    assert event["metadata"]

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

    assert event["review_status"] in {"kept", "inbox"}

    reviewed = store.update_event_review(event["id"], review_status="ignored")
    assert reviewed["review_status"] == "ignored"
    assert not store.recent_events()

    kept = store.update_event_review(event["id"], review_status="kept", importance=0.9)
    assert kept["current_importance"] == 0.9

    memory = pipeline.promote_event(event["id"])
    assert memory["text"] == kept["text"]
    assert memory["confidence"] == 0.9


def test_llm_config_and_prompt_contract(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store)
    pipeline.ingest_event(EventCreate(text="Open Memory 支持运行时选择 LLM。", source="test"))

    answer, events, memories = pipeline.query("运行时 LLM", llm_spec="none")
    prompt = build_prompt("运行时 LLM", events, memories)

    assert LLMConfig.from_spec("ollama:qwen2.5").provider == "ollama"
    assert create_llm_client(LLMConfig.from_spec("lmstudio:local-model")).model == "local-model"
    assert "当前未启用 LLM" in answer
    assert "Cite evidence" in prompt
    assert "occurred_at" in prompt
    assert "reason=" in prompt
    assert extract_openai_text({"output_text": "ok"}) == "ok"
    assert extract_chat_text({"choices": [{"message": {"content": "local ok"}}]}) == "local ok"


def test_ingest_assessment_uses_time_context():
    payload = EventCreate(
        text="明天必须继续做 Open Memory 的 iPhone VAD。",
        source="test",
        started_at="2026-06-12T08:30:00+08:00",
    )
    assessment = assess_event(payload, llm_spec="none")
    prompt = build_ingest_prompt(payload, assessment.assessed_at)

    assert assessment.importance_reason
    assert assessment.review_status in {"kept", "inbox", "ignored"}
    assert "occurred_at: 2026-06-12T08:30:00+08:00" in prompt


def test_parse_llm_ingest_assessment():
    assessment = parse_llm_assessment(
        """
        {
          "category": "project",
          "importance": 0.86,
          "tags": ["Open Memory", "iPhone"],
          "importance_reason": "Time-sensitive project follow-up.",
          "review_status": "kept"
        }
        """,
        assessed_at=datetime.now(timezone.utc),
    )

    assert assessment.category == "project"
    assert assessment.importance == 0.86
    assert assessment.review_status == "kept"


def test_query_rejects_unknown_llm_provider(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    pipeline = MemoryPipeline(store)

    try:
        pipeline.query("anything", llm_spec="missing:model")
    except ValueError as exc:
        assert "unsupported LLM provider" in str(exc)
    else:
        raise AssertionError("Expected invalid LLM provider to fail")


def test_lm_provider_error_is_reported(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return None

        def read(self):
            return b'{"error":"Compute error."}'

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())

    try:
        post_json("http://localhost:1234/v1/chat/completions", {})
    except LLMError as exc:
        assert "Compute error" in str(exc)
    else:
        raise AssertionError("Expected provider error to fail")
