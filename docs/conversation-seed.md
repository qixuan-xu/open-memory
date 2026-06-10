# Conversation Seed

This document captures the original product intent and early design decisions from the first Open Memory planning conversation.

## Product Vision

Open Memory is a personal AI memory system that records, organizes, summarizes, and understands a user's life, projects, learning, and ideas over time.

The goal is not to save everything forever. The goal is to distill what matters into a long-term memory layer that helps an AI agent understand:

- what the user is building
- what the user cares about
- how the user's goals change
- how the user tends to make decisions
- what the user may want to do next

The system should gradually become a useful digital twin, but with explicit memory layers, user correction, and privacy-aware defaults.

## Core Pipeline

```text
iPhone audio capture
-> VAD filters silence and low-value audio
-> Whisper or similar ASR transcribes speech
-> transcript events enter a timeline database
-> lightweight classification and importance scoring
-> daily summaries
-> long-term memory compression
-> self-reflection loop
-> AI agent answers with retrieval-backed context
```

The architecture should remain layered:

```text
raw capture -> transcript events -> daily summary -> long-term memory -> AI agent
```

Do not push all history into a model context window.

## Model Strategy

Open Memory should be model-provider agnostic.

Recommended division of labor:

- VAD: Silero VAD, iOS-native VAD, or similar.
- Transcription: WhisperKit on iPhone, faster-whisper on server, or cloud fallback.
- Lightweight classification: rules first, then small local model or embedding-based label matching.
- Embeddings: BGE-M3, OpenAI embeddings, or another multilingual embedding model.
- Vector database: Qdrant or Chroma.
- Reasoning and synthesis: GPT-class cloud models or Qwen-class local models.

Useful rule of thumb:

```text
small model/rules = organize
embedding = retrieve by meaning
large model = summarize, reason, reflect
database = timeline and provenance
```

## Dynamic Importance

Importance should not be decided once.

Initial event importance is only a first guess. The system should later reassess importance based on:

- repeated mentions
- later decisions
- project continuity
- user corrections
- daily summary context
- long-term memory conflicts or confirmations

Future schema should consider:

```text
initial_importance
current_importance
importance_reason
last_reassessed_at
```

Example: a low-importance ESP32 note may become important after multiple later conversations continue the same project direction.

## Morning And Evening Summaries

This can be a v2 feature.

Morning briefing:

- what matters today
- what was left over from yesterday
- which projects need attention
- what the system should remind the user to clarify

Evening review:

- what happened today
- what decisions were made
- what should become long-term memory
- what to revisit tomorrow

Current MVP keeps manual `Summarize Today` and `Reflect` buttons.

## Model Storage Policy

Whisper and other model weights should not be committed to Git.

Git should contain:

- source code
- model manifests
- install commands
- setup scripts
- `.env.example`
- Docker and packaging files

Git should not contain:

- Whisper weights
- Qwen weights
- embedding weights
- raw audio
- private transcripts
- SQLite memory databases
- API keys
- cache files

The repository keeps `models/.gitkeep` only as a placeholder.

## CLI And Homebrew Direction

Desired future installation path:

```bash
brew tap qixuan-xu/open-memory
brew install open-memory
open-memory setup
```

Model selection should happen in the CLI, not inside Homebrew:

```bash
open-memory models list
open-memory models install whisper-small
open-memory models install bge-m3
open-memory models install qwen3-1.7b
```

The current CLI creates config and model placeholders. Future versions should implement real downloads or imports.

## Vibe Coding Workflow

The project should support a vibe coding workflow:

- user provides direction, taste, and product instincts
- Codex handles implementation, tests, commits, and GitHub updates
- changes should be committed frequently enough to keep history readable
- commit author should remain the user's Git identity
- GitHub Desktop can be used as a visual review surface

Default local path:

```text
/Users/qixuanxu/Desktop/Projects/open-memory
```

GitHub repository:

```text
https://github.com/qixuan-xu/open-memory
```

## Near-Term Roadmap

1. Make the dashboard feel useful and polished.
2. Add real model download/import behavior.
3. Add dynamic importance reassessment.
4. Add morning and evening summary jobs.
5. Add Qdrant or Chroma semantic retrieval.
6. Add Whisper or faster-whisper transcription worker.
7. Add iPhone capture app with visible recording controls.
8. Add memory correction, deletion, and privacy rules.

