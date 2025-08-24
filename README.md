# 孟子义智能学习助手

一个基于Apple Watch常驻采集的智能学习助手项目，支持语音识别、AI对话和语音合成。

## 项目概述

**核心功能：** 手表采集+唤醒 → 导出最近20秒 → 传 iPhone → iPhone 上传 Mac mini → Whisper→Gemini（≤100字）→ Mac mini 做 TTS → 回传 Watch 播放

## 架构流程图

```
Watch(采集+唤醒+20s缓存) → WCSession.sendFile → iPhone(转发上传) → Mac mini(Whisper base→Gemini Flash→TTS) → iPhone转发音频给Watch → Watch播放
```

## 技术栈

### Apple Watch 端
- **WatchKit** - 界面框架
- **AVFoundation** - 音频采集
- **WatchConnectivity** - 与iPhone通信
- **Core Data** - 本地数据存储

### iPhone 端
- **WatchConnectivity** - 与iPhone通信
- **URLSession** - 网络请求
- **AVFoundation** - 音频处理

### Mac mini 服务端
- **Flask** - Web服务框架
- **Whisper** - 语音转文字
- **Gemini API** - 文本处理
- **TTS** - 文字转语音
- **WebSocket** - 实时通信

## 项目结构

```
mengziyi/
├── ziyi/                          # iOS客户端应用
│   ├── ziyiApp.swift              # 应用入口
│   ├── ContentView.swift          # 主界面
│   ├── ClassroomArchive/          # 课程录制模块
│   └── ziyiWatch Watch App/       # Apple Watch应用
├── menziyi-server/                # Flask后端服务器
│   ├── app.py                     # 应用入口
│   ├── api/                       # API接口
│   ├── core/                      # 核心功能
│   └── requirements.txt           # Python依赖
├── notes/                         # 笔记处理流水线
├── prompts/                       # AI提示词模板
├── tools/                         # 数据处理工具
└── 文档/                          # 项目文档
```

## 快速开始

### 1. 环境要求

- macOS 14.0+
- Xcode 15.0+
- Python 3.12+
- Apple Watch (可选)

### 2. 后端服务启动

```bash
# 进入后端目录
cd menziyi-server

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

### 3. iOS应用运行

```bash
# 打开Xcode项目
open ziyi/ziyi.xcodeproj

# 选择目标设备并运行
```

### 4. 烟雾测试

```bash
# 运行烟雾测试
./run_smoke_tests.sh
```

## 开发进度

### ✅ 已完成
- 基础架构搭建
- WatchConnectivity通信框架
- 音频采集模块
- Flask后端API
- Whisper语音识别集成
- Gemini API集成

### 🚧 进行中
- 20秒音频缓存机制
- 唤醒检测算法
- TTS文字转语音

### 📋 待完成
- 端到端完整流程测试
- 性能优化
- 生产环境部署

## 配置说明

### 环境变量

创建 `.env` 文件：

```bash
# 服务器配置
PORT=5001
APP_ENV=development
SECRET_KEY=your-secret-key

# 功能开关
CLASSROOM_MODE_ENABLED=1

# API密钥
GEMINI_API_KEY=your-gemini-api-key
```

### 功能开关

在 `ziyi/Config.swift` 中配置功能开关：

```swift
struct FeatureFlags {
    static let classroomModeEnabled = true
    // 其他功能开关...
}
```

## 测试

### 后端测试

```bash
cd menziyi-server
python test_smoke.py
```

### iOS测试

在Xcode中运行应用，进入烟雾测试页面进行本地测试。

## 部署

### 开发环境

```bash
# 后端
cd menziyi-server
python app.py

# iOS
# 在Xcode中运行到模拟器或设备
```

### 生产环境

1. 配置生产环境变量
2. 部署Flask应用到服务器
3. 配置反向代理和SSL
4. 打包iOS应用到App Store

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: [您的姓名]
- 邮箱: [您的邮箱]
- 项目链接: [https://github.com/mochiwang/mengziyi](https://github.com/mochiwang/mengziyi)

## 更新日志

### v0.1.0 (2025-01-20)
- 初始版本发布
- 基础架构搭建完成
- 核心功能模块实现
- 烟雾测试系统建立

---

**注意：** 本项目仍在积极开发中，API和功能可能会有变化。
