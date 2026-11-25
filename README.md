# linux-lab

Linux 操作系统实验二「Linux 环境系统开发与部署」的代码仓库，包含前三个实验的源码。

| 目录 | 内容 |
| --- | --- |
| `vscode/` | VS Code Remote-SSH 远程编译运行的 fork 示例（`gcc test.c -o test && ./test`） |
| `docker/` | 用静态编译 + `FROM scratch` 构建最小镜像的 Dockerfile 与源文件 |
| `ai/` | LeNet（PyTorch，CPU）训练 MNIST、单图推理、Flask 部署手写数字识别服务 |
| `llm/` | Ollama 的网页聊天服务（Flask 流式转发）与 200 行的 mini-agent |

## 环境

Ubuntu 22.04 LTS，Python 3.10，torch 2.9.1+cpu / torchvision 0.24.1+cpu，
Ollama 0.40.18 + Qwen3-1.7B-GGUF（ModelScope 源）。

## 快速开始

```bash
# 实验一：编译运行
cd vscode && gcc test.c -o test && ./test

# 实验一：构建并运行容器
cd docker && gcc -static -o hello hello.c && docker build -t hello-static:v1 . && docker run --rm hello-static:v1

# 实验二：训练 + 推理 + 部署
cd ai && python3 -m venv .venv && .venv/bin/pip install torch torchvision flask --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python train.py && .venv/bin/python test.py && .venv/bin/python serve.py

# 实验三：聊天服务与 Agent
cd llm && pip install flask openai && python serve.py
LLM_MODEL=qwen3:1.7b python agent.py
```
