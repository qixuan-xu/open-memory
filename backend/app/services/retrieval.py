from __future__ import annotations

import re
import sqlite3


def rank_rows(query: str, rows: list[sqlite3.Row], text_field: str = "text", limit: int = 8) -> list[sqlite3.Row]:
    query_terms = tokenize(query)
    if not query_terms:
        return rows[:limit]

    scored: list[tuple[float, sqlite3.Row]] = []
    for row in rows:
        text = row[text_field]
        terms = tokenize(text)
        overlap = len(query_terms & terms)
        if overlap == 0:
            continue
        importance = float(row["importance"]) if "importance" in row.keys() else float(row["confidence"])
        score = overlap + importance
        scored.append((score, row))

    return [row for _, row in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def synthesize_answer(question: str, events: list[sqlite3.Row], memories: list[sqlite3.Row]) -> str:
    if not events and not memories:
        return "我还没有找到足够相关的记忆。可以继续记录几天，或者换一个更具体的关键词再问。"

    lines = [f"问题：{question}", "", "根据目前记忆，我能推断："]

    if memories:
        lines.append("长期记忆里最相关的是：")
        for memory in memories[:3]:
            lines.append(f"- {memory['text']}")

    if events:
        lines.append("原始时间线里相关片段是：")
        for event in events[:4]:
            lines.append(f"- {event['created_at']} [{event['category']}]: {event['text']}")

    lines.append("")
    lines.append("这是基于检索结果的初步回答；接入 LLM 后，这一层会改成带引用的自然语言推理。")
    return "\n".join(lines)


def tokenize(text: str) -> set[str]:
    english = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    chinese = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    return set(english + chinese)

