import Foundation

enum APIError: Error { case badURL, badResp, server(String) }

final class APIClient {
    // 真机用 Mac 的局域网 IP；模拟器才用 127.0.0.1
    #if targetEnvironment(simulator)
    static let serverBase = "http://127.0.0.1:5001"
    #else
    static let serverBase = "http://10.0.0.133:5001" // ← 换成你 Mac 当前 IP
    #endif

    // 一个稳定的 URL 组装工具（防止 badURL & 漏 query）
    private static func endpoint(_ path: String, query: [String:String]? = nil) throws -> URL {
        guard var comp = URLComponents(string: serverBase) else { throw URLError(.badURL) }
        comp.path += path.hasPrefix("/") ? path : "/\(path)"
        if let q = query {
            comp.queryItems = q.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        guard let url = comp.url else { throw URLError(.badURL) }
        return url
    }

    static func uploadAudio(fileURL: URL, filename: String, courseId: String) async throws -> String {
        let url = try endpoint("/api/lessons/upload")
        var req = URLRequest(url: url); req.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        func app(_ s: String) { body.append(s.data(using: .utf8)!) }

        app("--\(boundary)\r\n")
        app("Content-Disposition: form-data; name=\"filename\"\r\n\r\n")
        app("\(filename)\r\n")

        app("--\(boundary)\r\n")
        app("Content-Disposition: form-data; name=\"course_id\"\r\n\r\n\(courseId)\r\n")

        let data = try Data(contentsOf: fileURL)
        app("--\(boundary)\r\n")
        app("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileURL.lastPathComponent)\"\r\n")
        app("Content-Type: audio/m4a\r\n\r\n")
        body.append(data); app("\r\n")
        app("--\(boundary)--\r\n")
        req.httpBody = body

        let (respData, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse else { throw APIError.badResp }
        guard (200..<300).contains(http.statusCode) else {
            throw APIError.server(String(data: respData, encoding: .utf8) ?? "upload failed")
        }
        let ok = try JSONDecoder().decode(UploadAccepted.self, from: respData)
        return ok.lesson_id
    }

    static func fetchStatus(lessonId: String) async throws -> LessonItem {
        let url = try endpoint("/api/lessons/status", query: ["lesson_id": lessonId])
        let (data, resp) = try await URLSession.shared.data(from: url)
        guard let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw APIError.badResp }
        
        // 使用 JSONDecoder 进行更优雅的解析，处理下划线到驼峰命名的映射
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        
        return try decoder.decode(LessonItem.self, from: data)
    }
}
