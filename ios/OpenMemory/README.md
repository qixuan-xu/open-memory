# Open Memory iOS Capture Scaffold

This folder contains the first iOS capture scaffold for Open Memory v1.

The product shape is an explicit Memory Session, not hidden always-on listening:

1. The user taps Start Memory Session.
2. iOS asks for microphone permission.
3. The app configures a background-capable audio session.
4. Audio is segmented locally.
5. VAD and transcription can run on-device later.
6. Transcript events are uploaded to the FastAPI `/events` endpoint.
7. The dashboard Memory Inbox decides what becomes long-term memory.

## Required Xcode Setup

Create a SwiftUI iOS app target, then add the files under `OpenMemory/`.

Enable capabilities:

- Background Modes: Audio, AirPlay, and Picture in Picture

Add Info.plist privacy strings:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Open Memory records only during explicit memory sessions so it can transcribe useful notes for your private memory inbox.</string>
<key>UIBackgroundModes</key>
<array>
  <string>audio</string>
</array>
```

For local backend testing from a physical iPhone, set `OPEN_MEMORY_API_BASE_URL` to a reachable LAN URL such as:

```text
http://192.168.1.20:8000
```

If you use plain HTTP during development, add an App Transport Security exception for that host. Production builds should use HTTPS.

## Next Implementation Steps

- Replace the placeholder segment flush with WhisperKit or server-side transcription.
- Add VAD before writing or uploading segments.
- Add an offline queue with retry and visible failure state.
- Surface battery, storage, and interruption safeguards.
