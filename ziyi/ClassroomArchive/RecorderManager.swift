import Foundation
import AVFoundation

// 误触保护 - 直接使用硬编码值，避免编译问题
private let __classroom_enabled = false  // 默认关闭，与Config.swift保持一致

final class RecorderManager: NSObject, ObservableObject, AVAudioRecorderDelegate {
    @Published var isRecording = false
    @Published var currentFileURL: URL?
    private var recorder: AVAudioRecorder?

    func start() throws {
        if !__classroom_enabled {
            print("[Classroom] disabled, ignoring recording start")
            return
        }
        
        let s = AVAudioSession.sharedInstance()
        try s.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
        try s.setActive(true)

        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let url = dir.appendingPathComponent("lesson_\(Int(Date().timeIntervalSince1970)).m4a")
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        recorder = try AVAudioRecorder(url: url, settings: settings)
        recorder?.delegate = self
        recorder?.record()
        isRecording = true
        currentFileURL = url
    }

    func stop() {
        if !__classroom_enabled {
            print("[Classroom] disabled, ignoring recording stop")
            return
        }
        
        recorder?.stop()
        isRecording = false
    }
}
