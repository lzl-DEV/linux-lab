#!/usr/bin/env python3
# mini-agent：一个类似 Codex / Claude Code 的极简命令行编程 Agent
# 原理：大模型负责“想”（决定调用哪个工具），本程序负责“做”（真正执行工具），循环往复直到任务完成
import json
import os
import subprocess
import sys

from openai import OpenAI

BASE_URL = os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1')
API_KEY = os.getenv('LLM_API_KEY', 'ollama')
MODEL = os.getenv('LLM_MODEL', 'qwen3:4b')

# Agent 只能在这个工作目录里读写文件、执行命令
WORKDIR = os.path.abspath(os.getenv('AGENT_WORKDIR', './workspace'))

# 设为 1 则执行命令前不再询问（有风险，谨慎使用）
AUTO_APPROVE = os.getenv('AGENT_AUTO', '0') == '1'

MAX_STEPS = 20  # 单个任务最多调用多少轮工具，防止死循环

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = f'''你是一个运行在 Linux 终端里的编程助手（Agent），可以通过工具操作电脑来完成用户的任务。
当前工作目录：{WORKDIR}，所有文件都放在这个目录里。
工作方法：
1. 每个新任务都必须亲自调用工具去做，不要只给用户讲怎么做。
   注意：你说的话不会改变电脑，只有调用工具才会。没有调用工具并看到成功的结果之前，绝不能说“已完成”。
2. 写代码用 write_file 工具，写完后用 run_shell 运行或编译，确认结果正确；出错就读错误信息并修改，直到成功。
3. 画图时用 Python 的 matplotlib 或 Pillow 把图片保存为 png 文件（不要用 plt.show() 弹窗）。
4. 不要运行需要人工交互或永不退出的命令（如 vim、top、启动服务器）。
5. 任务完成后，用简洁的中文告诉用户做了什么、生成了哪些文件，不要重复贴出全部代码。'''

# 工具说明书：告诉大模型有哪些工具可用、每个工具需要什么参数（JSON Schema 格式）
TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'run_shell',
            'description': '在工作目录下执行一条 bash 命令，返回输出和退出码。可用于运行程序、编译、安装依赖、查看文件等。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string', 'description': '要执行的 bash 命令'}
                },
                'required': ['command'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'write_file',
            'description': '创建或覆盖一个文件，写入完整内容。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': '文件路径（相对于工作目录）'},
                    'content': {'type': 'string', 'description': '文件的完整内容'},
                },
                'required': ['path', 'content'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'read_file',
            'description': '读取一个文本文件的内容。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': '文件路径（相对于工作目录）'}
                },
                'required': ['path'],
            },
        },
    },
]


# ---------------- 工具的真正实现 ----------------
def safe_path(path):
    # 把路径限制在工作目录内，防止 Agent 改到别处的文件
    full = os.path.abspath(os.path.join(WORKDIR, path))
    if os.path.commonpath([full, WORKDIR]) != WORKDIR:
        raise ValueError(f'路径 {path} 超出了工作目录')
    return full


def run_shell(command):
    if not AUTO_APPROVE:
        ok = input('\033[33m  允许执行该命令吗？[y/N] \033[0m').strip().lower()
        if ok != 'y':
            return '用户拒绝执行该命令。'
    # 让命令优先使用当前虚拟环境里的 python / pip
    env = dict(os.environ)
    env['PATH'] = os.path.dirname(sys.executable) + os.pathsep + env.get('PATH', '')
    try:
        r = subprocess.run(['bash', '-c', command], cwd=WORKDIR, env=env,
                           capture_output=True, text=True, timeout=120)
        output = (r.stdout + r.stderr).strip()
        # 输出太长会塞满模型的上下文，只保留末尾部分
        if len(output) > 4000:
            output = '...(前面省略)...\n' + output[-4000:]
        return f'退出码: {r.returncode}\n{output}'
    except subprocess.TimeoutExpired:
        return '命令执行超时（120 秒），已终止。'


def write_file(path, content):
    full = safe_path(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    return f'已写入 {path}（{len(content)} 个字符）'


def read_file(path):
    with open(safe_path(path), encoding='utf-8') as f:
        return f.read()[:8000]


FUNCTIONS = {'run_shell': run_shell, 'write_file': write_file, 'read_file': read_file}


def call_tool(name, arguments):
    # 执行大模型指定的工具，出错时把错误信息返回给模型，让它自己修正
    try:
        args = json.loads(arguments or '{}')
        return str(FUNCTIONS[name](**args))
    except Exception as e:
        return f'工具调用出错: {type(e).__name__}: {e}'


# ---------------- Agent 主循环 ----------------
def run_task(messages):
    used_tool = False  # 本次任务是否真正调用过工具
    nudged = False     # 是否已经提醒过模型
    for step in range(MAX_STEPS):
        # 1. 把对话历史 + 工具说明书发给大模型，让它决定下一步
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0.2,
        )
        msg = resp.choices[0].message

        # 把模型的回复（包括它要调用的工具）记入历史
        assistant_msg = {'role': 'assistant', 'content': msg.content or ''}
        if msg.tool_calls:
            assistant_msg['tool_calls'] = [
                {'id': tc.id, 'type': 'function',
                 'function': {'name': tc.function.name, 'arguments': tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        # 2. 模型没有调用工具 => 它认为任务完成了，输出最终回答
        if not msg.tool_calls:
            # 小模型常犯的两种错，发现了就提醒它一次：
            #   a. 只把代码贴在回复里，却没有真正写文件、运行
            #   b. 把工具调用写成普通文本 {"name": ..., "arguments": ...}，程序无法识别
            content = (msg.content or '').strip()
            if not nudged and (content.startswith('{') or (not used_tool and '```' in content)):
                print('\033[33m（模型没有正确调用工具，提醒它重试）\033[0m')
                messages.append({'role': 'user', 'content':
                                 '你还没有真正执行任何操作。请使用工具调用（function calling）功能，'
                                 '而不是把代码或 JSON 写在回复里，把任务实际做完。'})
                nudged = True
                continue
            print(f'\033[32mAgent> \033[0m{msg.content}\n')
            return

        # 3. 模型要求调用工具 => 由本程序执行，并把结果返回给模型
        used_tool = True
        for tc in msg.tool_calls:
            name, arguments = tc.function.name, tc.function.arguments
            print(f'\033[36m[{step + 1}] 调用工具 {name}\033[0m')
            try:
                shown = json.loads(arguments or '{}')
            except json.JSONDecodeError:
                shown = {'参数': arguments}
            if name == 'run_shell':
                print(f'  $ {shown.get("command")}')
            elif name in ('write_file', 'read_file'):
                print(f'  文件: {shown.get("path")}')
            else:
                print(f'  参数: {shown}')
            result = call_tool(name, arguments)
            print(f'\033[90m  结果: {result[:300]}\033[0m')
            messages.append({'role': 'tool', 'tool_call_id': tc.id, 'content': result})
    print(f'达到最大步数 {MAX_STEPS}，任务中止。\n')


def main():
    os.makedirs(WORKDIR, exist_ok=True)
    print(f'mini-agent  model: {MODEL} @ {BASE_URL}')
    print(f'工作目录: {WORKDIR}')
    print('输入任务开始，输入 exit 退出，输入 /reset 清空历史\n')
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    while True:
        try:
            task = input('你 > ').strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not task:
            continue
        if task == 'exit':
            break
        if task == '/reset':
            del messages[1:]
            print('（历史已清空）')
            continue
        messages.append({'role': 'user', 'content': task})
        run_task(messages)


if __name__ == '__main__':
    main()
