import Foundation
import WatchConnectivity

final class WatchBridge: NSObject, WCSessionDelegate {
    static let shared = WatchBridge()
    private let s = WCSession.default

    func start() {
        guard WCSession.isSupported() else { return }
        s.delegate = self
        s.activate()
        print("⌚️ watch WCSession.activate()")
    }

    // 激活结果（watchOS）
    func session(_ session: WCSession,
                 activationDidCompleteWith activationState: WCSessionActivationState,
                 error: Error?) {
        print("⌚️ watch activation:", activationState.rawValue, error?.localizedDescription ?? "nil")
    }

    // 收到 iPhone 的前台消息
    func session(_ session: WCSession, didReceiveMessage message: [String : Any]) {
        print("⌚️ watch didReceiveMessage:", message)
    }

    // 收到 iPhone 的后台投递
    func session(_ session: WCSession, didReceiveUserInfo userInfo: [String : Any] = [:]) {
        print("⌚️ watch didReceiveUserInfo:", userInfo)
    }
}
