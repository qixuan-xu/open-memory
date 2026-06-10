import Foundation

struct MemoryEventPayload: Encodable {
    let text: String
    let source: String
    let startedAt: Date?
    let endedAt: Date?
    let metadata: [String: String]

    enum CodingKeys: String, CodingKey {
        case text
        case source
        case startedAt = "started_at"
        case endedAt = "ended_at"
        case metadata
    }
}

struct MemoryEvent: Decodable, Identifiable {
    let id: Int
    let text: String
    let category: String
    let importance: Double
    let reviewStatus: String
    let source: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case text
        case category
        case importance
        case reviewStatus = "review_status"
        case source
        case createdAt = "created_at"
    }
}
