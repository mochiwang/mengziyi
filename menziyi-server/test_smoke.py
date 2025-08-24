#!/usr/bin/env python3
"""
后端烟雾测试脚本
测试健康检查和上传接口的基本功能
"""

import requests
import os
import sys
import time
from pathlib import Path

# 配置
BASE_URL = "http://localhost:5001"
HEALTH_ENDPOINT = f"{BASE_URL}/healthz"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/lessons/upload"

def test_health_check():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过 (200)")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_upload_endpoint():
    """测试上传接口"""
    print("🔍 测试上传接口...")
    
    # 创建一个测试音频文件
    test_audio_path = Path("test_smoke_audio.wav")
    
    # 生成一个简单的WAV文件头（1秒静音）
    wav_header = (
        b'RIFF' + (36).to_bytes(4, 'little') + b'WAVE' +
        b'fmt ' + (16).to_bytes(4, 'little') + (1).to_bytes(2, 'little') +
        (1).to_bytes(2, 'little') + (16000).to_bytes(4, 'little') +
        (32000).to_bytes(4, 'little') + (2).to_bytes(2, 'little') +
        (16).to_bytes(2, 'little') + b'data' + (0).to_bytes(4, 'little')
    )
    
    with open(test_audio_path, 'wb') as f:
        f.write(wav_header)
    
    try:
        with open(test_audio_path, 'rb') as f:
            files = {'file': ('test_smoke_audio.wav', f, 'audio/wav')}
            response = requests.post(UPLOAD_ENDPOINT, files=files, timeout=30)
        
        if response.status_code in [200, 201, 204]:
            print("✅ 上传接口通过 (204/200)")
            return True
        else:
            print(f"❌ 上传接口失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 上传接口异常: {e}")
        return False
    finally:
        # 清理测试文件
        if test_audio_path.exists():
            test_audio_path.unlink()

def main():
    """主测试函数"""
    print("🚀 开始后端烟雾测试...")
    print(f"目标服务器: {BASE_URL}")
    print("-" * 50)
    
    # 测试健康检查
    health_ok = test_health_check()
    
    # 测试上传接口
    upload_ok = test_upload_endpoint()
    
    print("-" * 50)
    print("📊 测试结果:")
    print(f"健康检查: {'✅ 通过' if health_ok else '❌ 失败'}")
    print(f"上传接口: {'✅ 通过' if upload_ok else '❌ 失败'}")
    
    if health_ok and upload_ok:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("💥 部分测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
