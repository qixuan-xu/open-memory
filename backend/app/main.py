from datetime import date

from fastapi import FastAPI

from backend.app.core.schemas import EventCreate, EventRead, QueryRequest, QueryResponse
from backend.app.services.pipeline import MemoryPipeline
from backend.app.services.reflection import ReflectionEngine


app = FastAPI(title="Allen Memory OS", version="0.1.0")
pipeline = MemoryPipeline()
reflection_engine = ReflectionEngine(pipeline.store)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "system": "Allen Memory OS"}


@app.post("/events", response_model=EventRead)
def create_event(payload: EventCreate):
    return row_to_event(pipeline.ingest_event(payload))


@app.get("/events", response_model=list[EventRead])
def list_events(limit: int = 50):
    return [row_to_event(row) for row in pipeline.store.recent_events(limit)]


@app.post("/summaries/{day}")
def summarize(day: date):
    row = pipeline.summarize_day(day)
    return {"day": row["day"], "summary": row["summary"], "categories": row["categories"]}


@app.post("/reflections/{day}")
def reflect(day: date):
    row = reflection_engine.reflect_on_day(day)
    return {"day": row["day"], "reflection": row["text"]}


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest):
    answer, events, memories = pipeline.query(payload.question, payload.limit)
    return {
        "answer": answer,
        "supporting_events": [row_to_event(row) for row in events],
        "supporting_memories": [dict(row) for row in memories],
    }


def row_to_event(row) -> dict:
    return {
        "id": row["id"],
        "text": row["text"],
        "category": row["category"],
        "importance": row["importance"],
        "source": row["source"],
        "created_at": row["created_at"],
    }

