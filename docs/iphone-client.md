# iPhone Client Plan

The iPhone app is the main capture device.

## v1 Product Shape

The first iPhone version should feel like an explicit Memory Session rather than hidden always-on listening.

- Start and pause recording from a clear control.
- Show a visible recording state whenever capture is active.
- Keep raw audio local and temporary by default.
- Run VAD before transcription or upload.
- Upload transcript events to the FastAPI Memory Inbox.
- Let the dashboard decide what is kept, ignored, deleted, or promoted to long-term memory.
- Pause or warn on low battery, low storage, phone calls, and audio route interruptions.

The starter SwiftUI scaffold lives in [`../ios/OpenMemory`](../ios/OpenMemory).

## v1 Capture Flow

```text
Start Memory Session
-> request microphone permission
-> configure background-capable audio session
-> capture audio buffers
-> VAD removes silence
-> WhisperKit or server worker transcribes speech
-> POST /events
-> Memory Inbox review
```

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
- Explicit user review before low-confidence content becomes long-term memory.
