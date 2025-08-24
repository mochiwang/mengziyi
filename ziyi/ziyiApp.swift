//
//  ziyiApp.swift
//  ziyi
//
//  Created by edison on 8/18/25.
//

import SwiftUI

@main
struct ziyiApp: App {
    init() {
        WCBridgePhone.shared.start()   // ← 启动与手表的会话
    }
    var body: some Scene {
        WindowGroup { ContentView() }
    }
}
