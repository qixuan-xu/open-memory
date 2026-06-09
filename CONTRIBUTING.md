# Contributing

Open Memory is meant to be hackable and local-first.

## Development

```bash
pip install -e ".[dev]"
pytest
uvicorn backend.app.main:app --reload
```

## Principles

- Keep memory layers explicit.
- Preserve source provenance.
- Prefer user-correctable memories over hidden assumptions.
- Make privacy controls visible.
- Keep the MVP runnable without paid APIs.

## Good First Issues

- Add Chroma retrieval provider.
- Add faster-whisper transcription worker.
- Add memory deletion endpoint.
- Add timeline export.
- Add iPhone SwiftUI capture prototype.
- Add a web dashboard for summaries and memory review.
