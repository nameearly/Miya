#!/bin/bash
# 弥娅 WSL 代理安装脚本
# 用法: bash install_agent.sh

set -e

echo "============================================"
echo "   弥娅 WSL 代理安装程序"
echo "============================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 创建工作目录
MIYA_DIR="$HOME/.miya"
mkdir -p "$MIYA_DIR"

echo "📁 创建工作目录: $MIYA_DIR"

# 创建 requirements.txt
cat > "$MIYA_DIR/requirements.txt" << 'EOF'
aiohttp>=3.8.0
requests>=2.28.0
python-dotenv>=0.19.0
EOF

# 创建主代理脚本
cat > "$MIYA_DIR/miya_agent.py" << 'PYEOF'
#!/usr/bin/env python3
"""
弥娅 WSL 代理 - 独立运行在 WSL 中
连接回 Windows 主系统
"""

import asyncio
import aiohttp
import os
import sys
import argparse
import json
from pathlib import Path

class WSLMiyaAgent:
    def __init__(self, session_id: str, host: str = "localhost", port: int = 8000):
        self.session_id = session_id
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.running = True
        
    async def connect(self):
        """连接到主系统"""
        print(f"🔗 正在连接到弥娅主系统 ({self.base_url})...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 发送注册请求
                async with session.post(
                    f"{self.base_url}/api/terminal/register",
                    json={
                        "session_id": self.session_id,
                        "platform": "wsl",
                        "username": os.environ.get("USER", "wsl_user")
                    }
                ) as resp:
                    if resp.status == 200:
                        print("✅ 已连接到弥娅主系统！")
                        return True
                    else:
                        print(f"❌ 连接失败: {resp.status}")
                        return False
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            return False
    
    async def send_message(self, message: str):
        """发送消息到主系统"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/terminal/chat",
                    json={
                        "session_id": self.session_id,
                        "message": message
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "")
                    return None
        except Exception as e:
            return f"错误: {e}"
    
    async def interactive_loop(self):
        """交互循环"""
        print("\n" + "="*50)
        print("  弥娅 WSL 代理已启动")
        print("  输入消息与弥娅对话，输入 'exit' 退出")
        print("="*50 + "\n")
        
        while self.running:
            try:
                user_input = input("你> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ["exit", "quit", "退出"]:
                    print("👋 再见！")
                    self.running = False
                    break
                
                # 发送消息并显示响应
                response = await self.send_message(user_input)
                if response:
                    print(f"\n弥娅> {response}\n")
                else:
                    print("\n❌ 发送失败\n")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                self.running = False
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

async def main():
    parser = argparse.ArgumentParser(description="弥娅 WSL 代理")
    parser.add_argument("--session-id", required=True, help="会话ID")
    parser.add_argument("--host", default="localhost", help="主系统地址")
    parser.add_argument("--port", type=int, default=8000, help="主系统端口")
    args = parser.parse_args()
    
    agent = WSLMiyaAgent(args.session_id, args.host, args.port)
    
    if await agent.connect():
        await agent.interactive_loop()
    else:
        print("❌ 无法连接到弥娅主系统，请确保主系统正在运行")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

chmod +x "$MIYA_DIR/miya_agent.py"

# 创建启动脚本
cat > "$MIYA_DIR/run.sh" << 'EOF'
#!/bin/bash
# 快速启动弥娅代理

SESSION_ID=${1:-$(uuidgen 2>/dev/null || echo "$$")}
HOST=${2:-"localhost"}
PORT=${3:-8000}

echo "启动弥娅 WSL 代理..."
echo "会话ID: $SESSION_ID"
echo "主系统: $HOST:$PORT"

python3 "$HOME/.miya/miya_agent.py" --session-id "$SESSION_ID" --host "$HOST" --port "$PORT"
EOF

chmod +x "$MIYA_DIR/run.sh"

# 安装依赖
echo "📦 安装依赖..."
pip3 install --user -q -r "$MIYA_DIR/requirements.txt" 2>/dev/null || \
    pip3 install --break-system-packages -q -r "$MIYA_DIR/requirements.txt" 2>/dev/null || true

echo ""
echo "============================================"
echo "✅ 安装完成！"
echo "============================================"
echo ""
echo "启动弥娅代理："
echo "  bash ~/.miya/run.sh"
echo ""
echo "或指定参数："
echo "  python3 ~/.miya/miya_agent.py --session-id 12345 --host 192.168.1.100"
echo ""
