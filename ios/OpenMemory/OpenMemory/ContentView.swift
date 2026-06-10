import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = CaptureViewModel()

    var body: some View {
        NavigationStack {
            Form {
                Section("Memory Session") {
                    HStack {
                        Circle()
                            .fill(viewModel.isRecording ? .green : .secondary)
                            .frame(width: 12, height: 12)
                        Text(viewModel.status)
                    }

                    Button(viewModel.isRecording ? "Pause Recording" : "Start Recording") {
                        if viewModel.isRecording {
                            viewModel.stopMemorySession()
                        } else {
                            Task { await viewModel.startMemorySession() }
                        }
                    }
                }

                Section("Manual Transcript Test") {
                    TextEditor(text: $viewModel.lastTranscript)
                        .frame(minHeight: 120)
                    Button("Send to Memory Inbox") {
                        Task { await viewModel.submitManualTranscript() }
                    }
                }
            }
            .navigationTitle("Open Memory")
        }
    }
}

#Preview {
    ContentView()
}
