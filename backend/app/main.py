from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.schemas import EventCreate, EventRead, EventReviewUpdate, QueryRequest, QueryResponse
from backend.app.services.pipeline import MemoryPipeline
from backend.app.services.reflection import ReflectionEngine


app = FastAPI(title="Open Memory", version="0.1.0")
pipeline = MemoryPipeline()
reflection_engine = ReflectionEngine(pipeline.store)
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "system": "Open Memory"}


@app.get("/")
def dashboard():
    return FileResponse("backend/app/static/index.html")


@app.post("/events", response_model=EventRead)
def create_event(payload: EventCreate):
    return row_to_event(pipeline.ingest_event(payload))


@app.get("/events", response_model=list[EventRead])
def list_events(limit: int = 50):
    return [row_to_event(row) for row in pipeline.store.recent_events(limit)]


@app.get("/events/inbox", response_model=list[EventRead])
def list_inbox_events(limit: int = 50):
    return [row_to_event(row) for row in pipeline.store.list_inbox_events(limit)]


@app.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventReviewUpdate):
    row = pipeline.store.update_event_review(
        event_id=event_id,
        review_status=payload.review_status,
        text=payload.text,
        importance=payload.importance,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return row_to_event(row)


@app.post("/events/{event_id}/promote")
def promote_event(event_id: int):
    row = pipeline.promote_event(event_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return dict(row)


@app.delete("/events/{event_id}")
def delete_event(event_id: int):
    if not pipeline.store.delete_event(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"deleted": True}


@app.get("/summaries")
def list_summaries(limit: int = 14):
    return [dict(row) for row in pipeline.store.recent_daily_summaries(limit)]


@app.get("/memories")
def list_memories(limit: int = 50):
    return [dict(row) for row in pipeline.store.list_long_term_memories(limit)]


@app.get("/reflections")
def list_reflections(limit: int = 14):
    return [dict(row) for row in pipeline.store.recent_reflections(limit)]


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
        "importance": row["current_importance"],
        "review_status": row["review_status"],
        "source": row["source"],
        "created_at": row["created_at"],
    }
