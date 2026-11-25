#!/usr/bin/env python3
# 网页聊天服务：Flask 后端转发请求给 Ollama，并把回答流式推送给浏览器
import os

from flask import Flask, Response, redirect, request
from openai import OpenAI

BASE_URL = os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1')
API_KEY = os.getenv('LLM_API_KEY', 'ollama')
MODEL = os.getenv('LLM_MODEL', 'qwen3:1.7b')

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
app = Flask(__name__)


@app.route('/')
def index():
    return redirect('/static/index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    # 前端把完整的对话历史 messages 发过来（服务端不保存状态）
    messages = request.get_json()['messages']
    messages = [{'role': 'system', 'content': '你是一个乐于助人的助手，请用简洁的中文回答。'}] + messages

    def generate():
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True,
            reasoning_effort='none',
        )
        for chunk in stream:
            yield chunk.choices[0].delta.content or ''

    # 以流的形式返回，浏览器边收边显示
    return Response(generate(), mimetype='text/plain; charset=utf-8')


if __name__ == '__main__':
    print(f'model: {MODEL} @ {BASE_URL}')
    app.run(host='0.0.0.0', port=5000, threaded=True)
