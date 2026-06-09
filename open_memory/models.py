from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelOption:
    key: str
    role: str
    label: str
    size: str
    note: str


MODEL_OPTIONS = [
    ModelOption("whisper-tiny", "transcription", "Whisper tiny", "~75 MB", "Fastest local transcription starter."),
    ModelOption("whisper-small", "transcription", "Whisper small", "~466 MB", "Better accuracy for daily capture."),
    ModelOption("bge-m3", "embedding", "BGE-M3", "~2.3 GB", "Multilingual semantic retrieval."),
    ModelOption("qwen3-1.7b", "reasoning", "Qwen3 1.7B", "~1.5 GB", "Small local memory classifier and summarizer."),
    ModelOption("cloud-gpt", "reasoning", "Cloud GPT provider", "API", "Best quality analysis, no local weights."),
]


PRESETS = {
    "light": ["whisper-tiny"],
    "balanced": ["whisper-small", "bge-m3"],
    "local-ai": ["whisper-small", "bge-m3", "qwen3-1.7b"],
    "cloud": ["whisper-small", "bge-m3", "cloud-gpt"],
}

