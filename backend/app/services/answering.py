from __future__ import annotations

import sqlite3

from open_memory.llms import LLMClient, NoLLMClient


def answer_with_llm(question: str, events: list[sqlite3.Row], memories: list[sqlite3.Row], llm: LLMClient) -> str:
    if isinstance(llm, NoLLMClient):
        return fallback_answer(question, events, memories)
    return llm.complete(build_prompt(question, events, memories))


def build_prompt(question: str, events: list[sqlite3.Row], memories: list[sqlite3.Row]) -> str:
    evidence = build_evidence(events, memories)
    return (
        "You answer using only the provided Open Memory evidence.\n"
        "If evidence is weak or missing, say so plainly.\n"
        "Cite evidence with bracket numbers like [M1] or [E1].\n\n"
        f"Question:\n{question}\n\n"
        f"Evidence:\n{evidence}\n\n"
        "Answer:"
    )


def build_evidence(events: list[sqlite3.Row], memories: list[sqlite3.Row]) -> str:
    lines: list[str] = []
    for index, memory in enumerate(memories, start=1):
        lines.append(
            f"[M{index}] {memory['text']} "
            f"(type={memory['memory_type']}, confidence={memory['confidence']}, source_day={memory['source_day']})"
        )
    for index, event in enumerate(events, start=1):
        lines.append(
            f"[E{index}] {event['text']} "
            f"(category={event['category']}, importance={event['current_importance']}, "
            f"created_at={event['created_at']})"
        )
    return "\n".join(lines) if lines else "No relevant memory evidence was found."


def fallback_answer(question: str, events: list[sqlite3.Row], memories: list[sqlite3.Row]) -> str:
    if not events and not memories:
        return "我还没有找到足够相关的记忆。可以继续记录几天，或者换一个更具体的关键词再问。"

    lines = [f"问题：{question}", "", "根据目前记忆，我找到这些相关证据："]
    for index, memory in enumerate(memories[:3], start=1):
        lines.append(f"[M{index}] {memory['text']}")
    for index, event in enumerate(events[:4], start=1):
        lines.append(f"[E{index}] {event['created_at']} [{event['category']}]: {event['text']}")
    lines.append("")
    lines.append("当前未启用 LLM；使用 --llm 或 OPEN_MEMORY_LLM 后，会基于这些证据生成带引用的自然语言回答。")
    return "\n".join(lines)
