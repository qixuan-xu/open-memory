# iPhone Client Plan

The iPhone app is the main capture device.

## First Version

- Manual recording button.
- Local VAD before upload.
- Upload transcript text to FastAPI.
- Show recent timeline and daily summary.
- Let user delete events.

## Second Version

- Background capture mode with explicit visible status.
- WhisperKit or server-side faster-whisper.
- Local encrypted queue for offline capture.
- Per-category privacy controls.

## API Contract

The app can start with:

```http
POST /events
Content-Type: application/json

{
  "text": "transcribed speech segment",
  "source": "iphone",
  "started_at": "2026-06-09T10:20:00+08:00",
  "ended_at": "2026-06-09T10:20:15+08:00",
  "metadata": {
    "vad": "silero",
    "transcriber": "whisper",
    "device": "iphone"
  }
}
```

## Privacy Defaults

- No raw audio storage by default.
- Clear recording indicator.
- Fast pause gesture.
- Delete from timeline and long-term memory.
- Export and wipe controls.

