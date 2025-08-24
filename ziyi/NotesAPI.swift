// zyi/NotesAPI.swift  (<200 行)
import Foundation

struct NoteChunk: Identifiable, Codable {
    var id: String { chunk_id }
    let chunk_id: String
    let processed: Bool
    let chars: Int
}
struct ChatCard: Identifiable, Codable {
    var id: String { chunk_id }
    let chunk_id: String
    let title: String
    let zh_explain: String
    let en_excerpt: String
    let score: Int
}
struct ChatResp: Codable { let status: String; let answer: String; let chunks: [ChatCard]; let suggested: [String] }

enum NotesAPI {
    static let base = APIClient.serverBase

    static func chunk(lessonId: String, maxChars: Int = 800) async throws -> Int {
        let url = URL(string: base + "/api/notes/chunk")!
        let body = ["lesson_id": lessonId, "max_chars": maxChars] as [String : Any]
        let (data, _) = try await jsonPOST(url: url, body: body)
        let obj = try JSONSerialization.jsonObject(with: data) as! [String:Any]
        return obj["chunks"] as? Int ?? 0
    }

    static func listChunks(lessonId: String) async throws -> [NoteChunk] {
        let url = URL(string: base + "/api/notes/chunks?lesson_id=\(lessonId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        let obj = try JSONSerialization.jsonObject(with: data) as! [String:Any]
        let items = obj["items"] as? [[String:Any]] ?? []
        let json = try JSONSerialization.data(withJSONObject: items)
        return try JSONDecoder().decode([NoteChunk].self, from: json)
    }

    static func fetchPrompt(lessonId: String, chunkId: String) async throws -> (String,String) {
        let url = URL(string: base + "/api/notes/chunk_text?lesson_id=\(lessonId)&chunk_id=\(chunkId)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        let obj = try JSONSerialization.jsonObject(with: data) as! [String:Any]
        return (obj["text"] as? String ?? "", obj["prompt"] as? String ?? "")
    }

    static func saveLabel(lessonId: String, jsonString: String) async throws {
        let url = URL(string: base + "/api/notes/label")!
        let data = jsonString.data(using: .utf8) ?? Data()
        let item = try JSONSerialization.jsonObject(with: data)
        let body: [String:Any] = ["lesson_id": lessonId, "item": item]
        _ = try await jsonPOST(url: url, body: body)
    }

    static func collect(lessonId: String) async throws -> Int {
        let url = URL(string: base + "/api/notes/collect")!
        let (data, _) = try await jsonPOST(url: url, body: ["lesson_id": lessonId])
        let obj = try JSONSerialization.jsonObject(with: data) as! [String:Any]
        return obj["items"] as? Int ?? 0
    }

    static func chat(lessonId: String, query: String, k: Int = 6) async throws -> ChatResp {
        let url = URL(string: base + "/api/chat")!
        let (data, _) = try await jsonPOST(url: url, body: ["lesson_id": lessonId, "query": query, "k": k])
        return try JSONDecoder().decode(ChatResp.self, from: data)
    }

    // MARK: - helpers
    private static func jsonPOST(url: URL, body: [String:Any]) async throws -> (Data, URLResponse) {
        var req = URLRequest(url: url); req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: body, options: [])
        return try await URLSession.shared.data(for: req)
    }
}
