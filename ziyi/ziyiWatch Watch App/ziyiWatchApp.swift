import SwiftUI

@main
struct ziyiWatchApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onAppear { WatchBridge.shared.start() } // ← 启动 WCSession
        }
    }
}
