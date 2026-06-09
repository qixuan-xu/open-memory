from backend.app.core.categories import Category


PROJECT_TERMS = {
    "esp32",
    "smt",
    "贴片机",
    "nas",
    "memory os",
    "vad",
    "whisper",
    "qwen",
    "fastapi",
}
SCHOOL_TERMS = {"history", "math", "school", "transfer", "转学", "申请", "学校", "数学", "历史"}
FAMILY_TERMS = {"family", "妈妈", "爸爸", "家里", "家庭", "父母"}
TODO_TERMS = {"todo", "待办", "要做", "需要", "记得", "明天", "下周"}
DECISION_TERMS = {"决定", "选择", "方案", "取舍", "prefer", "because", "原因"}
IDEA_TERMS = {"想法", "idea", "灵感", "可以做", "如果", "prototype", "vibe"}


def classify_text(text: str) -> tuple[Category, float, list[str]]:
    lowered = text.lower()
    hits: list[str] = []

    scores = {
        Category.PROJECT: _score(lowered, PROJECT_TERMS, hits),
        Category.SCHOOL: _score(lowered, SCHOOL_TERMS, hits),
        Category.FAMILY: _score(lowered, FAMILY_TERMS, hits),
        Category.TODO: _score(lowered, TODO_TERMS, hits),
        Category.DECISION: _score(lowered, DECISION_TERMS, hits),
        Category.IDEA: _score(lowered, IDEA_TERMS, hits),
    }

    category = max(scores, key=scores.get)
    if scores[category] == 0:
        category = Category.LIFE

    importance = estimate_importance(lowered, category, len(hits))
    return category, importance, sorted(set(hits))


def estimate_importance(text: str, category: Category, hit_count: int) -> float:
    score = 0.2 + min(hit_count * 0.12, 0.36)
    if category in {Category.DECISION, Category.TODO, Category.IDEA}:
        score += 0.18
    if any(marker in text for marker in ["重要", "关键", "决定", "deadline", "必须", "目标"]):
        score += 0.24
    if len(text) > 120:
        score += 0.08
    return round(min(score, 1.0), 2)


def _score(text: str, terms: set[str], hits: list[str]) -> int:
    score = 0
    for term in terms:
        if term.lower() in text:
            score += 1
            hits.append(term)
    return score

