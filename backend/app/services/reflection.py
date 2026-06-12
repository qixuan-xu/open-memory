from __future__ import annotations

from collections import Counter
from datetime import date
import sqlite3

from backend.app.services.store import MemoryStore


class ReflectionEngine:
    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def reflect_on_day(self, day: date) -> sqlite3.Row:
        events = self.store.list_events_for_day(day)
        memories = self.store.list_long_term_memories(50)
        text = self._build_reflection(day, events, memories)
        return self.store.save_reflection(day, text)

    def _build_reflection(self, day: date, events: list[sqlite3.Row], memories: list[sqlite3.Row]) -> str:
        if not events:
            return f"{day.isoformat()}: 今天没有足够材料进行反思。系统应继续等待更高质量输入。"

        category_counts = Counter(event["category"] for event in events)
        top_categories = ", ".join(f"{name}={count}" for name, count in category_counts.most_common())
        important = [event for event in events if float(event["current_importance"]) >= 0.6]
        projects = [event for event in events if event["category"] == "project"]
        decisions = [event for event in events if event["category"] == "decision"]

        lines = [
            f"# Reflection {day.isoformat()}",
            "",
            f"记录分布：{top_categories}",
            "",
            "## 自我观察",
        ]

        if projects:
            lines.append(f"- 今天项目相关内容较突出，共 {len(projects)} 条；系统应继续追踪这些项目的阶段变化。")
        if decisions:
            lines.append(f"- 今天出现 {len(decisions)} 条决策信号；后续问答应优先保留当时的理由和取舍。")
        if important:
            lines.append(f"- 有 {len(important)} 条高重要度记录，适合进入长期记忆候选池。")
        if not important:
            lines.append("- 今天多数内容偏低强度，适合只保留时间线，不必过度压缩进长期记忆。")

        lines.extend(["", "## 需要验证的假设"])
        if memories:
            lines.append("- 长期记忆已有积累，后续应检查新记录是否重复、冲突或更新旧偏好。")
        lines.append("- 当系统不确定某条记忆是否长期有效时，应生成一个澄清问题，而不是直接固化。")

        lines.extend(["", "## 下一步改进"])
        lines.append("- 增加用户反馈按钮：保留、合并、删除、标记错误。")
        lines.append("- 对项目类记忆加入状态字段：想法、调研、原型、进行中、暂停、完成。")
        lines.append("- 用向量检索替换当前 lexical retrieval，并保留可解释引用。")

        return "\n".join(lines)
