from datetime import date

from backend.app.core.schemas import EventCreate
from backend.app.services.answering import build_prompt
from backend.app.services.pipeline import MemoryPipeline
from backend.app.services.reflection import ReflectionEngine
from backend.app.services.store import MemoryStore
from open_memory.llms import LLMConfig, create_llm_client, extract_chat_text, extract_openai_text


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
    assert extract_openai_text({"output_text": "ok"}) == "ok"
    assert extract_chat_text({"choices": [{"message": {"content": "local ok"}}]}) == "local ok"
