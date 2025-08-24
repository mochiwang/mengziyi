import SwiftUI
import AVFoundation

struct SmokeTestView: View {
    @StateObject private var smokeTest = SmokeTestManager()
    
    var body: some View {
        VStack(spacing: 20) {
            Text("烟雾测试")
                .font(.title)
                .fontWeight(.bold)
            
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("录音状态:")
                    Spacer()
                    Text(smokeTest.isRecording ? "🔴 录音中" : "⚪️ 未录音")
                        .foregroundColor(smokeTest.isRecording ? .red : .gray)
                }
                
                HStack {
                    Text("测试结果:")
                    Spacer()
                    Text(smokeTest.testResult)
                        .foregroundColor(smokeTest.testResult.contains("成功") ? .green : .red)
                }
                
                if let filePath = smokeTest.savedFilePath {
                    HStack {
                        Text("保存路径:")
                        Spacer()
                        Text(filePath)
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }
            }
            .padding()
            .background(Color.gray.opacity(0.1))
            .cornerRadius(10)
            
            Button(action: {
                smokeTest.runSmokeTest()
            }) {
                HStack {
                    Image(systemName: "play.circle.fill")
                    Text("运行烟雾测试")
                }
                .foregroundColor(.white)
                .padding()
                .background(Color.blue)
                .cornerRadius(10)
            }
            .disabled(smokeTest.isRecording)
            
            if smokeTest.isRecording {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle())
                    .scaleEffect(1.2)
            }
            
            Spacer()
        }
        .padding()
        .navigationTitle("烟雾测试")
    }
}

class SmokeTestManager: ObservableObject {
    @Published var isRecording = false
    @Published var testResult = "未测试"
    @Published var savedFilePath: String?
    
    private var audioRecorder: AVAudioRecorder?
    
    func runSmokeTest() {
        testResult = "测试中..."
        isRecording = true
        
        // 请求录音权限
        AVAudioSession.sharedInstance().requestRecordPermission { [weak self] granted in
            DispatchQueue.main.async {
                if granted {
                    self?.startRecording()
                } else {
                    self?.testResult = "❌ 录音权限被拒绝"
                    self?.isRecording = false
                }
            }
        }
    }
    
    private func startRecording() {
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playAndRecord, mode: .default)
            try audioSession.setActive(true)
            
            // 获取文档目录
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let audioFilename = documentsPath.appendingPathComponent("smoke_test_\(Int(Date().timeIntervalSince1970)).m4a")
            
            // 录音设置
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 44100,
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
            ]
            
            audioRecorder = try AVAudioRecorder(url: audioFilename, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.record()
            
            // 1秒后停止录音
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
                self?.stopRecording()
            }
            
        } catch {
            DispatchQueue.main.async {
                self.testResult = "❌ 录音启动失败: \(error.localizedDescription)"
                self.isRecording = false
            }
        }
    }
    
    private func stopRecording() {
        audioRecorder?.stop()
        isRecording = false
        
        if let url = audioRecorder?.url {
            savedFilePath = url.lastPathComponent
            testResult = "✅ 烟雾测试成功！录音已保存到沙盒"
        } else {
            testResult = "❌ 录音保存失败"
        }
    }
}

extension SmokeTestManager: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        DispatchQueue.main.async {
            if flag {
                self.savedFilePath = recorder.url.lastPathComponent
                self.testResult = "✅ 烟雾测试成功！录音已保存到沙盒"
            } else {
                self.testResult = "❌ 录音完成但保存失败"
            }
            self.isRecording = false
        }
    }
    
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        DispatchQueue.main.async {
            self.testResult = "❌ 录音编码错误: \(error?.localizedDescription ?? "未知错误")"
            self.isRecording = false
        }
    }
}

#Preview {
    SmokeTestView()
}
