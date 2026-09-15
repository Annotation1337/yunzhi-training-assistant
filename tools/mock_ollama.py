# -*- coding: utf-8 -*-
"""
Mock Ollama 服务器（仅用于本地测试）
======================================
模拟 Ollama 的 /api/tags 和 /api/chat 端点，
用于在无法访问外网的环境下端到端验证 llm_engine.py 的 RAG 链路。

这不是生产代码，仅测试用。
"""

from flask import Flask, request, jsonify
import sys

app = Flask(__name__)

MOCK_MODEL = "qwen2.5:3b"


@app.route("/api/tags", methods=["GET"])
def tags():
    return jsonify({"models": [{"name": MOCK_MODEL}, {"name": "llama3.1:8b"}]})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    messages = data.get("messages", [])
    # 提取 user 消息作为回答依据
    user_msg = ""
    for m in messages:
        if m.get("role") == "user":
            user_msg = m.get("content", "")
    # 模拟 LLM：基于用户消息里的"参考片段"生成一个固定格式回答
    answer = (
        f"【Mock 模型回答】已收到你的问题，并参考了 {user_msg.count('参考片段')} 个知识库片段。\n\n"
        f"建议：根据本地实训知识库相关内容进行配置，具体参数请以课堂指导书为准。"
    )
    return jsonify({"message": {"role": "assistant", "content": answer}})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 11434
    app.run(host="127.0.0.1", port=port, debug=False)
