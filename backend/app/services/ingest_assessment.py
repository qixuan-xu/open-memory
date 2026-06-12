from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os

from backend.app.core.categories import Category
from backend.app.core.schemas import EventCreate
from backend.app.services.classifier import classify_text
from open_memory.llms import LLMConfig, LLMError, NoLLMClient, create_llm_client


@dataclass(frozen=True)
class IngestAssessment:
    category: Category
    importance: float
    tags: list[str]
    importance_reason: str
    review_status: str
    assessed_at: datetime
    assessed_by: str


def assess_event(payload: EventCreate, llm_spec: str | None = None) -> IngestAssessment:
    assessed_at = datetime.now(timezone.utc).replace(microsecond=0)
    llm_spec = llm_spec or os.getenv("OPEN_MEMORY_INGEST_LLM") or os.getenv("OPEN_MEMORY_LLM")
    llm = create_llm_client(LLMConfig.from_spec(llm_spec))
    if not isinstance(llm, NoLLMClient):
        try:
            return parse_llm_assessment(llm.complete(build_ingest_prompt(payload, assessed_at)), assessed_at)
        except (LLMError, ValueError, json.JSONDecodeError, TypeError, KeyError):
            pass
    return heuristic_assessment(payload, assessed_at)


def heuristic_assessment(payload: EventCreate, assessed_at: datetime) -> IngestAssessment:
    category, importance, tags = classify_text(payload.text)
    if importance >= 0.72:
        review_status = "kept"
    elif importance <= 0.18:
        review_status = "ignored"
    else:
        review_status = "inbox"
    return IngestAssessment(
        category=category,
        importance=importance,
        tags=tags,
        importance_reason=build_rule_reason(category, importance, tags, payload),
        review_status=review_status,
        assessed_at=assessed_at,
        assessed_by="heuristic",
    )


def build_ingest_prompt(payload: EventCreate, assessed_at: datetime) -> str:
    occurred_at = payload.started_at or payload.ended_at or assessed_at
    return (
        "You are Open Memory's ingestion triage model.\n"
        "Given a user memory event and its time context, decide how important it is for future memory.\n"
        "Use the time context: a decision, commitment, project update, repeated theme, or time-sensitive plan is more important than casual noise.\n"
        "Return only valid JSON with these keys:\n"
        "- category: one of project, school, family, idea, todo, decision, life\n"
        "- importance: number from 0 to 1\n"
        "- tags: short array of strings\n"
        "- importance_reason: one concise sentence\n"
        "- review_status: one of kept, inbox, ignored\n\n"
        "Use review_status=kept for clearly useful long-term material, inbox for uncertain material, ignored for obvious noise.\n\n"
        f"assessed_at: {assessed_at.isoformat()}\n"
        f"occurred_at: {occurred_at.isoformat()}\n"
        f"source: {payload.source}\n"
        f"metadata: {json.dumps(payload.metadata, ensure_ascii=False, sort_keys=True)}\n"
        f"text: {payload.text}\n"
    )


def parse_llm_assessment(raw: str, assessed_at: datetime) -> IngestAssessment:
    data = json.loads(extract_json_object(raw))
    category = Category(str(data["category"]).lower())
    importance = clamp_importance(float(data["importance"]))
    tags = [str(tag).strip() for tag in data.get("tags", []) if str(tag).strip()][:8]
    review_status = str(data.get("review_status", "inbox")).lower()
    if review_status not in {"kept", "inbox", "ignored"}:
        review_status = "inbox"
    reason = str(data.get("importance_reason") or "LLM assessed this memory from content and time context.").strip()
    return IngestAssessment(
        category=category,
        importance=importance,
        tags=tags,
        importance_reason=reason[:240],
        review_status=review_status,
        assessed_at=assessed_at,
        assessed_by="llm",
    )


def extract_json_object(raw: str) -> str:
    stripped = raw.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM assessment did not contain a JSON object")
    return stripped[start : end + 1]


def clamp_importance(value: float) -> float:
    return round(min(max(value, 0), 1), 2)


def build_rule_reason(category: Category, importance: float, tags: list[str], payload: EventCreate) -> str:
    time_hint = payload.started_at or payload.ended_at
    parts = [f"Rule estimate: category={category.value}, importance={importance:.2f}"]
    if tags:
        parts.append(f"matched tags={', '.join(tags[:5])}")
    if time_hint:
        parts.append(f"event time={time_hint.isoformat()}")
    return "; ".join(parts)
