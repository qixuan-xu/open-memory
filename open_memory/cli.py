from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from backend.app.services.pipeline import MemoryPipeline
from backend.app.services.store import MemoryStore
from open_memory.models import MODEL_OPTIONS, PRESETS


APP_DIR = Path.home() / ".open-memory"
MODELS_DIR = APP_DIR / "models"
CONFIG_PATH = APP_DIR / "config.json"


def main() -> None:
    parser = argparse.ArgumentParser(prog="open-memory", description="Run and configure Open Memory.")
    sub = parser.add_subparsers(dest="command")

    setup = sub.add_parser("setup", help="Create local config and choose a model preset.")
    setup.add_argument("--preset", choices=sorted(PRESETS), default="balanced")

    start = sub.add_parser("start", help="Start the local Open Memory server.")
    start.add_argument("--llm", default=None, help="LLM backend: none, ollama:<model>, lmstudio:<model>, or openai:<model>.")

    ask = sub.add_parser("ask", help="Ask a question using stored memories.")
    ask.add_argument("question")
    ask.add_argument("--llm", default=None, help="LLM backend: none, ollama:<model>, lmstudio:<model>, or openai:<model>.")
    ask.add_argument("--limit", type=int, default=8)

    models = sub.add_parser("models", help="Manage optional local models.")
    model_sub = models.add_subparsers(dest="models_command")
    model_sub.add_parser("list", help="List known model options.")
    install = model_sub.add_parser("install", help="Mark a model as installed or planned.")
    install.add_argument("model", choices=[option.key for option in MODEL_OPTIONS])

    args = parser.parse_args()
    if args.command == "setup":
        setup_config(args.preset)
    elif args.command == "start":
        start_server(args.llm)
    elif args.command == "ask":
        return ask_question(args.question, args.limit, args.llm)
    elif args.command == "models" and args.models_command == "list":
        list_models()
    elif args.command == "models" and args.models_command == "install":
        install_model(args.model)
    else:
        parser.print_help()


def setup_config(preset: str) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "preset": preset,
        "models": PRESETS[preset],
        "models_dir": str(MODELS_DIR),
        "database": str(APP_DIR / "open_memory.sqlite3"),
    }
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Open Memory configured: {CONFIG_PATH}")
    print(f"Preset: {preset}")
    print("Models:")
    for key in PRESETS[preset]:
        print(f"  - {key}")


def list_models() -> None:
    for option in MODEL_OPTIONS:
        print(f"{option.key:15} {option.role:13} {option.size:8} {option.label} - {option.note}")


def install_model(model: str) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    marker = MODELS_DIR / f"{model}.planned"
    marker.write_text(
        "This is a placeholder. Future versions will download or import the model here.\n",
        encoding="utf-8",
    )
    print(f"Marked {model} in {MODELS_DIR}")
    print("Model weights are intentionally not committed to Git.")


def ask_question(question: str, limit: int, llm: str | None) -> None:
    try:
        pipeline = MemoryPipeline(MemoryStore(configured_database_path()))
        answer, events, memories = pipeline.query(question, limit, llm)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(answer)
    if events or memories:
        print()
        print("Citations:")
        for index, memory in enumerate(memories, start=1):
            print(f"[M{index}] long_term_memories:{memory['id']} source_day={memory['source_day']}")
        for index, event in enumerate(events, start=1):
            print(f"[E{index}] events:{event['id']} created_at={event['created_at']}")


def configured_database_path() -> Path:
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return Path(config["database"])
    return Path(os.getenv("ALLEN_MEMORY_DB", "./allen_memory.sqlite3"))


def start_server(llm: str | None = None) -> None:
    env = os.environ.copy()
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        env["ALLEN_MEMORY_DB"] = config["database"]
    if llm:
        env["OPEN_MEMORY_LLM"] = llm
    cmd = ["uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
