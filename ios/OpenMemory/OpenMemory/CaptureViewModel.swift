import AVFoundation
import Foundation

@MainActor
final class CaptureViewModel: ObservableObject {
    @Published private(set) var isRecording = false
    @Published private(set) var status = "Ready"
    @Published var lastTranscript = ""

    private let audioEngine = AVAudioEngine()
    private let api = MemoryAPI()
    private var sessionStartedAt: Date?

    func startMemorySession() async {
        guard !isRecording else { return }

        do {
            try await requestMicrophoneAccess()
            try configureAudioSession()
            try startAudioEngine()
            sessionStartedAt = Date()
            isRecording = true
            status = "Memory session active"
        } catch {
            status = "Unable to start recording: \(error.localizedDescription)"
        }
    }

    func stopMemorySession() {
        guard isRecording else { return }
        audioEngine.inputNode.removeTap(onBus: 0)
        audioEngine.stop()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        isRecording = false
        status = "Paused"
    }

    func submitManualTranscript() async {
        let text = lastTranscript.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        await uploadTranscript(text, startedAt: sessionStartedAt, endedAt: Date(), transcriber: "manual")
        lastTranscript = ""
    }

    private func requestMicrophoneAccess() async throws {
        let granted = await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { allowed in
                continuation.resume(returning: allowed)
            }
        }
        if !granted {
            throw CaptureError.microphoneDenied
        }
    }

    private func configureAudioSession() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .spokenAudio, options: [.allowBluetooth])
        try session.setActive(true)
    }

    private func startAudioEngine() throws {
        let input = audioEngine.inputNode
        let format = input.outputFormat(forBus: 0)
        input.installTap(onBus: 0, bufferSize: 4096, format: format) { _, _ in
            // VAD and transcription will run here in the next pass.
        }
        audioEngine.prepare()
        try audioEngine.start()
    }

    private func uploadTranscript(
        _ text: String,
        startedAt: Date?,
        endedAt: Date?,
        transcriber: String
    ) async {
        do {
            _ = try await api.createEvent(
                MemoryEventPayload(
                    text: text,
                    source: "iphone",
                    startedAt: startedAt,
                    endedAt: endedAt,
                    metadata: [
                        "capture_mode": "memory_session",
                        "transcriber": transcriber,
                        "vad": "pending"
                    ]
                )
            )
            status = "Uploaded to Memory Inbox"
        } catch {
            status = "Upload failed: \(error.localizedDescription)"
        }
    }
}

enum CaptureError: LocalizedError {
    case microphoneDenied

    var errorDescription: String? {
        switch self {
        case .microphoneDenied:
            return "Microphone access was denied."
        }
    }
}
