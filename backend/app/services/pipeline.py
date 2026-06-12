from __future__ import annotations

from datetime import date, datetime

from backend.app.core.schemas import EventCreate
from backend.app.services.classifier import classify_text
from backend.app.services.answering import answer_with_llm
from backend.app.services.retrieval import rank_rows
from backend.app.services.store import MemoryStore
from backend.app.services.summarizer import build_daily_summary, extract_long_term_candidates
from open_memory.llms import LLMConfig, create_llm_client


class MemoryPipeline:
    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def ingest_event(self, payload: EventCreate):
        category, importance, tags = classify_text(payload.text)
        return self.store.add_event(
            text=payload.text,
            category=category.value,
            importance=importance,
            source=payload.source,
            tags=tags,
            metadata=payload.metadata,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
        )

    def summarize_day(self, day: date):
        events = self.store.list_events_for_day(day)
        summary, categories = build_daily_summary(day, events)
        row = self.store.save_daily_summary(day, summary, categories)
        for candidate in extract_long_term_candidates(day, events):
            self.store.add_long_term_memory(
                memory_type=candidate["memory_type"],
                text=candidate["text"],
                confidence=candidate["confidence"],
                source_day=day,
            )
        return row

    def promote_event(self, event_id: int):
        event = self.store.get_event(event_id)
        if event is None:
            return None
        source_day = datetime.fromisoformat(event["created_at"]).date()
        confidence = max(0.6, min(float(event["current_importance"]), 0.95))
        memory = self.store.add_long_term_memory(
            memory_type=event["category"],
            text=event["text"],
            confidence=confidence,
            source_day=source_day,
        )
        self.store.update_event_review(event_id, review_status="kept", importance=confidence)
        return memory

    def query(self, question: str, limit: int = 8, llm_spec: str | None = None) -> tuple[str, list, list]:
        events = rank_rows(question, self.store.recent_events(200), limit=limit)
        memories = rank_rows(
            question,
            self.store.list_long_term_memories(200),
            text_field="text",
            limit=limit,
        )
        llm = create_llm_client(LLMConfig.from_spec(llm_spec))
        return answer_with_llm(question, events, memories, llm), events, memories
