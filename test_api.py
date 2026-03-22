#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试终端API
"""

import requests
import json

print("=" * 60)
print("测试弥娅终端API")
print("=" * 60)

# 测试状态API
try:
    print("1. 测试状态API...")
    response = requests.get("http://localhost:8000/api/status", timeout=5)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"   响应: {response.text[:200]}")
        print("   [OK] 状态API正常")
    else:
        print(f"   [ERROR] 状态API返回错误: {response.text}")
except Exception as e:
    print(f"   [ERROR] 状态API测试失败: {e}")

# 测试终端聊天API
try:
    print("\n2. 测试终端聊天API...")
    data = {
        "message": "你好",
        "session_id": "test123",
        "from_terminal": "test_terminal"
    }
    
    response = requests.post(
        "http://localhost:8000/api/terminal/chat",
        json=data,
        timeout=10
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print("   [OK] 终端聊天API正常")
    else:
        print(f"   [ERROR] 终端聊天API返回错误: {response.text}")
except Exception as e:
    print(f"   [ERROR] 终端聊天API测试失败: {e}")

# 测试终端历史API
try:
    print("\n3. 测试终端历史API...")
    response = requests.get(
        "http://localhost:8000/api/terminal/history?limit=5",
        timeout=5
    )
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print("   [OK] 终端历史API正常")
    else:
        print(f"   [ERROR] 终端历史API返回错误: {response.text}")
except Exception as e:
    print(f"   [ERROR] 终端历史API测试失败: {e}")

print("\n" + "=" * 60)
print("[OK] API测试完成！")
print("=" * 60)