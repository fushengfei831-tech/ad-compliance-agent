"""
Dify Agent 交互式流式调用客户端 (Streaming Agent Client)
======================================================
功能：通过 Server-Sent Events (SSE) 协议调用 Dify 本地/线上部署的
     “电商合规与文案重构”智能体，实现终端多轮交互、审查与安全改写。
"""

import os
import sys
import json
import requests

# 修复 Windows 控制台中文与 Emoji 打印编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# API 配置 (优先读取环境变量，避免密钥泄露)
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://localhost/v1")
DIFY_API_KEY = os.getenv("DIFY_AGENT_API_KEY", "your-agent-api-key-here")

def chat_with_agent(query: str, user_id: str = "compliance_operator", conversation_id: str = None):
    """
    流式调用 Dify Agent，实时打印思考过程与最终文案回答。
    """
    url = f"{DIFY_BASE_URL.rstrip('/')}/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "streaming",  # Dify Agent 强制要求 streaming 模式
        "user": user_id,
        "conversation_id": conversation_id or ""
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=120)
        if response.status_code != 200:
            print(f"\n[错误] 请求失败，HTTP 状态码: {response.status_code}")
            print(response.text)
            return None

        print("\n" + "=" * 60)
        print(f"🤖 待审文案: {query}")
        print("=" * 60 + "\n")

        new_conv_id = None
        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if not line_str.startswith("data: "):
                continue

            try:
                data = json.loads(line_str[6:])
                event = data.get("event")
                if not new_conv_id and data.get("conversation_id"):
                    new_conv_id = data.get("conversation_id")

                # 实时捕获并输出 Agent 的正文答复
                if event in ("agent_message", "message"):
                    print(data.get("answer", ""), end="", flush=True)

            except json.JSONDecodeError:
                continue

        print("\n\n" + "-" * 60)
        return new_conv_id

    except requests.exceptions.ConnectionError:
        print("\n[错误] 无法连接到 Dify 服务，请检查本地 Docker 服务是否正常运行 (http://localhost)。")
        return None
    except Exception as e:
        print(f"\n[异常] 请求发生错误: {e}")
        return None

if __name__ == "__main__":
    test_query = "这款美白精华7天彻底消除黄褐斑"
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])

    print(f"[*] 启动 Dify Agent 交互客户端...")
    print(f"[*] 服务端点: {DIFY_BASE_URL}")
    chat_with_agent(test_query)
