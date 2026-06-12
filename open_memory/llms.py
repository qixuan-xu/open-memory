from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


DEFAULT_LLM = "none"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_OPENAI_URL = "https://api.openai.com/v1/responses"


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str | None = None

    @classmethod
    def from_spec(cls, spec: str | None = None) -> "LLMConfig":
        selected = spec or os.getenv("OPEN_MEMORY_LLM") or os.getenv("ALLEN_MEMORY_LLM") or DEFAULT_LLM
        selected = selected.strip()
        if selected == DEFAULT_LLM:
            return cls(provider=DEFAULT_LLM)
        if ":" not in selected:
            raise ValueError("LLM must be 'none' or '<provider>:<model>'")
        provider, model = selected.split(":", maxsplit=1)
        if not provider or not model:
            raise ValueError("LLM must include both provider and model")
        return cls(provider=provider.lower(), model=model)


class NoLLMClient:
    def complete(self, prompt: str) -> str:
        raise LLMError("No LLM backend is configured")


class OllamaClient:
    def __init__(self, model: str, url: str | None = None) -> None:
        self.model = model
        self.url = url or os.getenv("OLLAMA_URL") or DEFAULT_OLLAMA_URL

    def complete(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        response = post_json(self.url, payload)
        text = response.get("response")
        if not isinstance(text, str):
            raise LLMError("Ollama response did not contain text")
        return text.strip()


class OpenAIResponsesClient:
    def __init__(self, model: str, url: str | None = None, api_key: str | None = None) -> None:
        self.model = model
        self.url = url or os.getenv("OPENAI_RESPONSES_URL") or DEFAULT_OPENAI_URL
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMError("OPENAI_API_KEY is required for openai:<model>")
        payload = {"model": self.model, "input": prompt}
        response = post_json(self.url, payload, headers={"Authorization": f"Bearer {self.api_key}"})
        return extract_openai_text(response)


def create_llm_client(config: LLMConfig) -> LLMClient:
    if config.provider == "none":
        return NoLLMClient()
    if config.provider == "ollama" and config.model:
        return OllamaClient(config.model)
    if config.provider == "openai" and config.model:
        return OpenAIResponsesClient(config.model)
    raise ValueError(f"unsupported LLM provider: {config.provider}")


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise LLMError(f"LLM request failed: {exc}") from exc

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM response was not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise LLMError("LLM response was not a JSON object")
    return decoded


def extract_openai_text(response: dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    fragments: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                fragments.append(content["text"])

    text = "".join(fragments).strip()
    if not text:
        raise LLMError("OpenAI response did not contain text")
    return text
