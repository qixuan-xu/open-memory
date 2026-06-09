# Architecture

Open Memory uses layered memory instead of a single giant prompt.

## Layers

1. Raw capture
   - iPhone records audio locally.
   - VAD removes silence and low-value audio.
   - The app uploads only speech segments or local transcripts.

2. Transcript timeline
   - Every transcript segment becomes an event.
   - Events keep timestamp, source, category, importance, tags, and metadata.

3. Daily summary
   - Events are grouped by day.
   - The summary preserves project work, decisions, plans, ideas, and commitments.

4. Long-term memory
   - High-signal daily items are compressed into durable memory records.
   - Each record keeps type, confidence, source day, and provenance.

5. Reflection loop
   - The system reviews the day and its current memory state.
   - It writes observations, hypotheses, gaps, and next improvements.

6. Agent answers
   - A question retrieves relevant events and long-term memories.
   - The LLM answers with citations instead of relying on hidden context.

## Service Boundaries

- `classifier.py`: local categorization and importance scoring.
- `summarizer.py`: daily summary and long-term memory candidate extraction.
- `reflection.py`: self-review and system improvement notes.
- `retrieval.py`: query-time retrieval, currently lexical and later vector-backed.
- `store.py`: SQLite persistence layer.
- `pipeline.py`: orchestration layer.

## Upgrade Points

- Replace `classifier.py` with an LLM or small local classifier.
- Replace `retrieval.py` with Chroma, Qdrant, or pgvector.
- Replace `summarizer.py` with GPT-5, Qwen, or a hybrid local/cloud model.
- Add background jobs with APScheduler, Celery, Dramatiq, or Temporal.
- Add encrypted sync once the iPhone app exists.
