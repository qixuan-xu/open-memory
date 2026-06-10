# Open Memory

Open Memory is a personal AI memory system that turns ambient phone capture into a layered, searchable, self-improving memory base.

The project is designed around one principle: do not stuff a lifetime into a model context window. Build a memory pipeline instead.

```text
phone audio -> VAD segments -> transcript events -> timeline -> daily summaries
          -> long-term memories -> reflection loop -> AI agent answers
```

## What This MVP Does

- Stores timestamped memory events in SQLite.
- Classifies events into projects, school, family, ideas, todos, decisions, and general life.
- Generates daily summaries from raw transcript text.
- Promotes useful facts into a long-term memory layer.
- Runs a self-reflection automation that produces:
  - observed patterns
  - preference hypotheses
  - project momentum notes
  - questions the system should ask later
- Answers memory questions with lexical retrieval today, ready to swap for Chroma or Qdrant later.

This first version does not save raw audio by default. It assumes the iPhone app or a recorder worker sends text segments after VAD and transcription.

## Quick Start

```bash
cd /Users/qixuanxu/Desktop/Projects/open-memory
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn backend.app.main:app --reload
```

Open:

- API docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>
- Dashboard: <http://127.0.0.1:8000/>

Docker:

```bash
docker compose up --build
```

CLI:

```bash
open-memory setup --preset balanced
open-memory models list
open-memory models install whisper-small
open-memory start
```

Model weights are not committed to Git. The CLI currently creates local config and model placeholders under `~/.open-memory`; future versions will download or import Whisper, embedding, and local reasoning models there.

Planned Homebrew flow:

```bash
brew tap qixuan-xu/open-memory
brew install open-memory
open-memory setup
```

Seed a memory event:

```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天继续研究 ESP32 的语音采集方案，感觉 VAD 要先在手机端做，避免服务器存太多无意义音频。",
    "source": "manual"
  }'
```

Generate today summary and reflection:

```bash
python scripts/run_reflection.py
```

Ask a question:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "我之前对 ESP32 采集方案是什么看法？"}'
```

## Roadmap

The original product intent and early architecture notes live in [`docs/conversation-seed.md`](docs/conversation-seed.md).

1. iPhone App capture
   - background audio capture
   - on-device VAD
   - encrypted upload of speech segments
   - user-controlled pause and delete controls

2. Transcription workers
   - Whisper local mode
   - faster-whisper server mode
   - cloud transcription fallback

3. Memory intelligence
   - Chroma or Qdrant vector retrieval
   - long-term memory deduplication
   - confidence scores and source provenance
   - memory correction workflow

4. Agent layer
   - conversational memory QA
   - daily planning agent
   - project historian
   - personal decision mirror

5. Privacy and safety
   - local-first defaults
   - per-category retention
   - encrypted storage
   - private redaction rules
   - explicit memory deletion and audit log

## Philosophy

Open Memory should slowly learn:

- what you care about
- what you are building
- how your goals change
- how you make decisions
- which patterns help or hurt you

The aim is not perfect surveillance. The aim is a useful second mind that gets better because it reflects, compresses, checks itself, and asks better questions.
