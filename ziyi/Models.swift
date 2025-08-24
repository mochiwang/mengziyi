import Foundation

struct LessonItem: Identifiable, Codable {
    let id: String
    let filename: String
    let state: String
    let textPreview: String?
    let durationSec: Double?
    let courseId: String?
}

struct UploadAccepted: Codable {
    let status: String
    let lesson_id: String
    let course_id: String
}
