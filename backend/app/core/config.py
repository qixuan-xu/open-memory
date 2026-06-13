from functools import lru_cache
from pathlib import Path
import os


class Settings:
    def __init__(self) -> None:
        self.database_path = Path(os.getenv("OPEN_MEMORY_DB", "./open_memory.sqlite3"))
        self.llm_provider = os.getenv("OPEN_MEMORY_LLM_PROVIDER", "heuristic")
        self.vector_provider = os.getenv("OPEN_MEMORY_VECTOR_PROVIDER", "lexical")


@lru_cache
def get_settings() -> Settings:
    return Settings()
