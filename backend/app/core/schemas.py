from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    text: str = Field(min_length=1)
    source: str = "manual"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
    llm: str | None = None


class EventRead(BaseModel):
    id: int
    text: str
    category: str
    importance: float
    importance_reason: str
    review_status: str
    source: str
    assessed_by: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime


class EventReviewUpdate(BaseModel):
    review_status: Literal["inbox", "kept", "ignored"] | None = None
    text: str | None = Field(default=None, min_length=1)
    importance: float | None = Field(default=None, ge=0, le=1)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=30)
    llm: str | None = None


class QueryResponse(BaseModel):
    answer: str
    supporting_events: list[EventRead]
    supporting_memories: list[dict]
