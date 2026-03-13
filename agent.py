import os
import sys
import json
import requests
from dotenv import load_dotenv
import argparse
from pathlib import Path
import traceback

load_dotenv('.env.agent.secret')
REQUIRED_VARS = ['LLM_API_KEY', 'LLM_API_BASE', 'LLM_MODEL']
config = {}
missing = []
for var in REQUIRED_VARS:
    value = os.getenv(var)
    if not value:
        missing.append(var)
    config[var.lower()] = value
if missing:
    print(f"Error: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)
PROJECT_ROOT = Path(__file__).parent.absolute()
MAX_TOOL_CALLS = 10
def read_file(path):
    try:
        full_path = (PROJECT_ROOT / path).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT)):
            return f"Error: Access denied - path outside project: {path}"
        if not full_path.exists():
            return f"Error: File not found: {path}"
        if not full_path.is_file():
            return f"Error: Not a file: {path}"
        return full_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error reading file: {str(e)}"
def list_files(path):
    try:
        full_path = (PROJECT_ROOT / path).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT)):
            return f"Error: Access denied - path outside project: {path}"
        if not full_path.exists():
            return f"Error: Path not found: {path}"
        if not full_path.is_dir():
            return f"Error: Not a directory: {path}"
        items = sorted([p.name for p in full_path.iterdir()])
        return '\n'.join(items) if items else "(empty)"
    except Exception as e:
        return f"Error listing files: {str(e)}"
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root"
                    }
                },
                "required": ["path"]
            }
        }
    }
]
def call_llm(messages):
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    api_base = config['api_base'].rstrip('/')
    url = f"{api_base}/chat/completions"
    payload = {
        "model": config['model'],
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling LLM: {e}", file=sys.stderr)
        sys.exit(1)
def execute_tool(tool_call):
    name = tool_call['function']['name']
    args = json.loads(tool_call['function']['arguments'])
    if name == 'read_file':
        result = read_file(args['path'])
    elif name == 'list_files':
        result = list_files(args['path'])
    else:
        result = f"Error: Unknown tool '{name}'"
    return {
        "role": "tool",
        "tool_call_id": tool_call['id'],
        "content": result
    }
def run_agent(question):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a documentation assistant. Answer questions using the project wiki. "
                "First use list_files to see what's in the wiki directory. "
                "Then use read_file on relevant files. "
                "When you find the answer, include the source reference (file path and section). "
                "Format: wiki/filename.md#section-name"
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]
    tool_calls_log = []
    for _ in range(MAX_TOOL_CALLS):
        response = call_llm(messages)
        choice = response['choices'][0]
        message = choice['message']
        if 'tool_calls' not in message or not message['tool_calls']:
            answer = message.get('content', '')
            source = extract_source(answer)
            output = {
                "answer": answer,
                "source": source,
                "tool_calls": tool_calls_log
            }
            print(json.dumps(output, ensure_ascii=False))
            return
        messages.append(message)
        for tool_call in message['tool_calls']:
            tool_result = execute_tool(tool_call)
            messages.append(tool_result)
            tool_calls_log.append({
                "tool": tool_call['function']['name'],
                "args": json.loads(tool_call['function']['arguments']),
                "result": tool_result['content']
            })
    answer = "Maximum tool calls reached without final answer"
    output = {
        "answer": answer,
        "source": "",
        "tool_calls": tool_calls_log
    }
    print(json.dumps(output, ensure_ascii=False))
def extract_source(text):
    import re
    match = re.search(r'(wiki/[a-zA-Z0-9_-]+\.md(?:#[a-zA-Z0-9_-]+)?)', text)
    return match.group(1) if match else ""
def main():
    parser = argparse.ArgumentParser(description='Documentation agent with tools')
    parser.add_argument('question', help='Question about the project')
    args = parser.parse_args()
    try:
        run_agent(args.question)
    except Exception as e:
        print(json.dumps({
            "answer": f"Error: {str(e)}",
            "source": "",
            "tool_calls": []
        }, ensure_ascii=False))
        sys.exit(1)
if __name__ == '__main__':
    main()
