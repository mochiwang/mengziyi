// zyi/StudyChatView.swift  (<200 行)
import SwiftUI

// 误触保护 - 直接使用硬编码值，避免编译问题
private let __classroom_enabled = false  // 默认关闭，与Config.swift保持一致

struct StudyChatView: View {
    let lessonId: String
    @State private var chunks: [NoteChunk] = []
    @State private var query = ""
    @State private var messages: [Message] = []
    @State private var working = false
    @State private var copiedPrompt: String = ""
    @State private var showPaste = false

    struct Message: Identifiable { 
        let id = UUID()
        let isUser: Bool
        let text: String
        let cards: [ChatCard]
    }

    var body: some View {
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
            .navigationTitle("学习助手")
        } else {
            VStack(spacing: 10) {
                header
                Divider()
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 16) {
                        ForEach(messages) { m in
                            bubble(m)
                        }
                    }.padding(.horizontal)
                }
                if !copiedPrompt.isEmpty {
                    Text("已复制一段到剪贴板，去窗口版 GPT 粘贴，拿到 JSON 后点下面『粘回 JSON』")
                        .font(.footnote).foregroundColor(.secondary).padding(.horizontal)
                }
                controls
            }
            .navigationTitle("学习助手")
            .onAppear { Task { await refresh() } }
            .sheet(isPresented: $showPaste) { 
                PasteJSONSheet(lessonId: lessonId, onSaved: { Task { await afterPaste() }})
            }
        }
    }

    var header: some View {
        HStack {
            let un = chunks.filter { !$0.processed }.count
            let done = chunks.count - un
            Text("未处理：\(un)  已处理：\(done)").font(.subheadline)
            Spacer()
            Button("刷新") { Task { await refresh() } }
            Button("自动切片") { Task { await doChunk() } }
        }.padding(.horizontal)
    }

    var controls: some View {
        VStack(spacing: 8) {
            HStack {
                TextField("问：这节课讲了什么 / 解释 epsilon-delta…", text: $query)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                Button(working ? "…" : "发送") { Task { await ask() } }
                    .disabled(query.trimmingCharacters(in: .whitespaces).isEmpty || working)
            }.padding(.horizontal)

            HStack {
                Button("复制下一段给 GPT") { Task { await copyNextPrompt() } }
                    .disabled(working)
                Button("粘回 JSON") { showPaste = true }
            }.padding(.horizontal).padding(.bottom, 6)
        }
    }

    func bubble(_ m: Message) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(m.text)
                .padding(10)
                .background(m.isUser ? Color.blue.opacity(0.15) : Color.gray.opacity(0.12))
                .cornerRadius(10)
            if !m.cards.isEmpty {
                ForEach(m.cards) { c in
                    DisclosureGroup("\(c.title)  (\(c.chunk_id))") {
                        Text(c.zh_explain).font(.body).padding(.bottom, 4)
                        Text(c.en_excerpt).font(.caption).foregroundColor(.secondary)
                    }.padding(8).background(Color.secondary.opacity(0.08)).cornerRadius(8)
                }
            }
        }
    }

    // MARK: actions
    func refresh() async {
        do { 
            let newChunks = try await NotesAPI.listChunks(lessonId: lessonId)
            await MainActor.run { chunks = newChunks }
        } catch { 
            print(error) 
        }
    }
    
    func doChunk() async {
        await MainActor.run { working = true }
        do { 
            _ = try await NotesAPI.chunk(lessonId: lessonId)
            await refresh() 
        } catch { 
            print(error) 
        }
        await MainActor.run { working = false }
    }
    
    func ask() async {
        await MainActor.run { working = true }
        defer { 
            Task { await MainActor.run { working = false } }
        }
        
        let currentQuery = query
        await MainActor.run { 
            messages.append(.init(isUser: true, text: currentQuery, cards: []))
            query = ""
        }
        
        do {
            let r = try await NotesAPI.chat(lessonId: lessonId, query: currentQuery)
            await MainActor.run {
                messages.append(.init(isUser: false, text: r.answer, cards: r.chunks))
            }
        } catch { 
            await MainActor.run {
                messages.append(.init(isUser: false, text: "出错：\(error.localizedDescription)", cards: []))
            }
        }
    }
    
    func copyNextPrompt() async {
        if let next = chunks.first(where: { !$0.processed }) {
            do {
                let (_, prompt) = try await NotesAPI.fetchPrompt(lessonId: lessonId, chunkId: next.chunk_id)
                UIPasteboard.general.string = prompt
                await MainActor.run { copiedPrompt = prompt }
            } catch { 
                print(error) 
            }
        } else {
            await MainActor.run { copiedPrompt = "" }
        }
    }
    
    func afterPaste() async {
        await MainActor.run { copiedPrompt = "" }
        do { 
            _ = try await NotesAPI.collect(lessonId: lessonId) 
        } catch { 
            print(error)
        }
        await refresh()
    }
}

// 粘贴回 JSON 的小面板
struct PasteJSONSheet: View {
    let lessonId: String
    var onSaved: () -> Void
    @Environment(\.dismiss) var dismiss
    @State private var text: String = UIPasteboard.general.string ?? ""

    var body: some View {
        NavigationView {
            VStack {
                TextEditor(text: $text).font(.system(.body, design: .monospaced))
                    .padding().border(Color.gray.opacity(0.3))
                HStack {
                    Button("保存") { Task { await save() } }.buttonStyle(.borderedProminent)
                    Button("取消") { dismiss() }
                }.padding()
            }.navigationTitle("粘回 JSON（单个片段）")
        }
    }
    
    func save() async {
        do { 
            try await NotesAPI.saveLabel(lessonId: lessonId, jsonString: text)
            onSaved()
            await MainActor.run { dismiss() }
        } catch { 
            print(error) 
        }
    }
}
