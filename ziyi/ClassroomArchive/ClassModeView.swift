import SwiftUI

// 误触保护 - 直接使用硬编码值，避免编译问题
private let __classroom_enabled = false  // 默认关闭，与Config.swift保持一致

struct ClassModeView: View {
    @StateObject private var rec = RecorderManager()
    @State private var filenameInput = ""
    @State private var lessons: [LessonItem] = []
    @State private var timer: Timer?

    var body: some View {
        NavigationStack {
            if !__classroom_enabled {
                VStack {
                    Text("课堂模式已关闭")
                        .font(.title)
                        .foregroundColor(.secondary)
                    Text("请在Config.swift中启用FeatureFlags.classroomModeEnabled")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding()
                }
                .navigationTitle("课堂模式")
            } else {
                VStack(spacing: 12) {
                    HStack {
                        Button(rec.isRecording ? "停止录音" : "开始录音") {
                            Task { 
                                if rec.isRecording {
                                    rec.stop() 
                                } else {
                                    try? await rec.start() 
                                }
                            }
                        }
                        .padding(.trailing, 8)

                        if let url = rec.currentFileURL, !rec.isRecording {
                            TextField("文件名 (A-Z a-z 0-9 _ -)", text: $filenameInput)
                                .textFieldStyle(.roundedBorder)
                                .frame(minWidth: 200)
                            Button("上传") { 
                                Task { await upload(url: url) }
                            }
                            .disabled(filenameInput.trimmingCharacters(in: .whitespaces).isEmpty)
                        }
                    }.padding(.horizontal)

                    List(lessons) { item in
                        HStack(alignment: .top) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("\(item.filename)  [\(item.state)]").font(.headline)
                                if let d = item.durationSec, item.state == "done" {
                                    Text(String(format: "时长: %.1f 秒", d)).font(.subheadline)
                                }
                                if let p = item.textPreview, item.state == "done" {
                                    Text(p).font(.body).lineLimit(3)
                                }
                            }
                            Spacer()
                            // ✅ 跳到学习助手（用该课的 lessonId）
                            if item.state == "done" {
                                NavigationLink("学习") {
                                    StudyChatView(lessonId: item.id)
                                }
                                .buttonStyle(.bordered)
                            }
                        }
                    }
                }
                .navigationTitle("课堂模式")
            }
        }
        .onDisappear { stopPolling() }
    }

    private func upload(url: URL) async {
        let fname = filenameInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !fname.isEmpty else { return }
        
        do {
            let id = try await APIClient.uploadAudio(fileURL: url, filename: fname, courseId: "CS101")
            await MainActor.run {
                lessons.insert(LessonItem(id: id, filename: fname, state: "queued",
                                          textPreview: nil, durationSec: nil, courseId: "CS101"), at: 0)
            }
            startPolling()
        } catch { 
            print("upload failed:", error) 
        }
    }

    private func startPolling() {
        stopPolling()
        timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            Task {
                // ✅ await 调用 + 在主线程写回
                for i in lessons.indices {
                    if lessons[i].state == "done" || lessons[i].state == "error" { continue }
                    do {
                        let fresh = try await APIClient.fetchStatus(lessonId: lessons[i].id)
                        await MainActor.run { lessons[i] = fresh }
                    } catch { 
                        print("poll failed:", error, "lessonId=\(lessons[i].id)")
                    }
                }
            }
        }
    }

    private func stopPolling() { 
        timer?.invalidate()
        timer = nil 
    }
}
