from __future__ import annotations

from collections import defaultdict
from datetime import date
import re
import sqlite3


def build_daily_summary(day: date, events: list[sqlite3.Row]) -> tuple[str, dict[str, int]]:
    if not events:
        return f"{day.isoformat()} 没有记录到可总结的内容。", {}

    by_category: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for event in events:
        by_category[event["category"]].append(event)

    lines = [f"# {day.isoformat()} Daily Memory Summary", ""]
    category_counts = {category: len(items) for category, items in by_category.items()}

    for category, items in sorted(by_category.items()):
        lines.append(f"## {category}")
        for event in sorted(items, key=lambda row: row["importance"], reverse=True)[:5]:
            lines.append(f"- {compress_sentence(event['text'])}")
        lines.append("")

    key_events = sorted(events, key=lambda row: row["importance"], reverse=True)[:5]
    lines.append("## Signals")
    for event in key_events:
        lines.append(f"- importance {event['importance']:.2f}: {compress_sentence(event['text'])}")

    return "\n".join(lines).strip(), category_counts


def extract_long_term_candidates(day: date, events: list[sqlite3.Row]) -> list[dict]:
    candidates: list[dict] = []
    for event in events:
        text = event["text"]
        category = event["category"]
        importance = float(event["importance"])
        lowered = text.lower()

        if importance < 0.5:
            continue

        memory_type = "observation"
        confidence = min(0.95, importance)
        if category == "project":
            memory_type = "project_history"
        elif category == "decision":
            memory_type = "decision_pattern"
        elif category == "idea":
            memory_type = "idea"
        elif category == "todo":
            memory_type = "commitment"

        if any(word in lowered for word in ["目标", "goal", "想要", "希望"]):
            memory_type = "goal"
            confidence = max(confidence, 0.78)

        candidates.append(
            {
                "memory_type": memory_type,
                "text": normalize_memory_text(text, day),
                "confidence": round(confidence, 2),
            }
        )

    return candidates


def compress_sentence(text: str, max_chars: int = 150) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "..."


def normalize_memory_text(text: str, day: date) -> str:
    return f"{day.isoformat()}: {compress_sentence(text, 220)}"

