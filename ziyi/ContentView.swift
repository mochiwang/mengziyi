//
//  ContentView.swift
//  ziyi
//
//  Created by edison on 8/18/25.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationStack {
            if FeatureFlags.classroomModeEnabled {
                ClassModeView()           // ← 课堂页
                    .navigationTitle("孟子义")
            } else {
                // 课堂模式关闭时的默认界面
                VStack(spacing: 20) {
                    Text("孟子义")
                        .font(.largeTitle)
                        .padding()
                    Text("课堂模式已关闭")
                        .foregroundColor(.secondary)
                    
                    NavigationLink(destination: SmokeTestView()) {
                        HStack {
                            Image(systemName: "testtube.2")
                            Text("烟雾测试")
                        }
                        .foregroundColor(.white)
                        .padding()
                        .background(Color.orange)
                        .cornerRadius(10)
                    }
                }
                .navigationTitle("孟子义")
            }
        }
    }
}

#Preview {
    ContentView()
}
