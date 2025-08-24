import SwiftUI
import WatchConnectivity

struct ContentView: View {
    var body: some View {
        VStack(spacing: 12) {
            Text("Hello Apple Watch")
            Button("Ping iPhone") {
                let s = WCSession.default
                if s.isReachable {
                    s.sendMessage(["ping": "watch"], replyHandler: { reply in
                        print("⌚️ got reply:", reply)
                    }, errorHandler: { err in
                        print("⌚️ send error:", err.localizedDescription)
                    })
                } else {
                    s.transferUserInfo(["ping":"watch"])
                    print("⌚️ not reachable → sent via transferUserInfo")
                }
            }
        }
    }
}
