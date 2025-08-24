# 孟子易服务器

一个基于 Flask 和 Whisper 的音频转写服务器，用于处理课程录音并生成文字转写。

## 功能特性

- 支持多种音频格式上传 (wav, mp3, m4a, aac)
- 使用 OpenAI Whisper 进行中文语音转写
- 异步转写处理，支持状态查询
- SQLite 数据库存储课程信息
- RESTful API 接口

## 安装依赖

```bash
pip install -r requirements.txt
```

## 系统要求

- Python 3.8+
- ffmpeg (用于音频处理)

### 安装 ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 运行服务器

```bash
python app.py
```

服务器将在 `http://localhost:5000` 启动。

## API 接口

### 1. 上传课程录音
```
POST /api/lessons/upload
Content-Type: multipart/form-data

file: 音频文件
```

### 2. 查询转写状态
```
GET /api/lessons/status/<lesson_id>
```

### 3. 获取所有课程
```
GET /api/lessons/list
```

### 4. 删除课程
```
DELETE /api/lessons/<lesson_id>
```

## 项目结构

```
menziyi-server/
│ app.py                # Flask 入口
│ api_lessons.py        # 上传 & 状态接口
│ db.py                 # SQLite 封装
│ transcriber.py        # Whisper 转写逻辑
│ utils_time.py         # 时间相关小工具
│ utils_media.py        # ffmpeg/文件处理小工具
│ requirements.txt      # Python 依赖
│ README.md            # 项目说明
│
├── data/
│   └── lessons/        # 存放录音和转写结果
│
└── db/
    └── index.sqlite    # SQLite 数据库（自动生成）
```

## 转写状态说明

- `uploaded`: 文件已上传，等待转写
- `transcribing`: 正在转写中
- `completed`: 转写完成
- `failed`: 转写失败

## 注意事项

1. 首次运行时会自动下载 Whisper 模型，需要网络连接
2. 建议使用 tiny 模型以获得更快的转写速度
3. 音频文件大小限制为 16MB
4. 数据库文件会在首次运行时自动创建
