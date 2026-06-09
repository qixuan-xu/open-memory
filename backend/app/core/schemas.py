from datetime import datetime
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    text: str = Field(min_length=1)
    source: str = "manual"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class EventRead(BaseModel):
    id: int
    text: str
    category: str
    importance: float
    source: str
    created_at: datetime


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=30)


class QueryResponse(BaseModel):
    answer: str
    supporting_events: list[EventRead]
    supporting_memories: list[dict]

