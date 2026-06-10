import Foundation

final class MemoryAPI {
    private let baseURL: URL
    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    init(
        baseURL: URL = URL(string: Bundle.main.object(forInfoDictionaryKey: "OPEN_MEMORY_API_BASE_URL") as? String ?? "http://127.0.0.1:8000")!,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.session = session
        self.encoder = JSONEncoder()
        self.encoder.dateEncodingStrategy = .iso8601
        self.decoder = JSONDecoder()
        self.decoder.dateDecodingStrategy = .iso8601
    }

    func createEvent(_ payload: MemoryEventPayload) async throws -> MemoryEvent {
        var request = URLRequest(url: baseURL.appending(path: "events"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(payload)

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw MemoryAPIError.requestFailed
        }
        return try decoder.decode(MemoryEvent.self, from: data)
    }
}

enum MemoryAPIError: Error {
    case requestFailed
}
