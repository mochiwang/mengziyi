// ziyi/WCBridgePhone.swift
import WatchConnectivity

final class WCBridgePhone: NSObject, WCSessionDelegate {
    static let shared = WCBridgePhone()
    private let sess = WCSession.default

    func start() {
        guard WCSession.isSupported() else { return }
        sess.delegate = self
        sess.activate()
    }

    // 收到手表的 ping
    func session(_ session: WCSession, didReceiveMessage message: [String : Any],
                 replyHandler: @escaping ([String : Any]) -> Void) {
        if message["ping"] as? String == "watch" {
            replyHandler(["pong": "iphone"])
        }
    }

    // 协议必需的空实现
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) { sess.activate() }
    func sessionReachabilityDidChange(_ session: WCSession) {}
    
    // iOS 必需的激活完成回调
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {}
}
