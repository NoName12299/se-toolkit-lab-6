import os
import sys
import json
import requests
from dotenv import load_dotenv
import argparse
from pathlib import Path
import traceback


load_dotenv('.env.agent.secret')
load_dotenv('.env.docker.secret')
print("LMS_API_KEY:", os.getenv('LMS_API_KEY'), file=sys.stderr)
print("LLM_API_KEY:", os.getenv('LLM_API_KEY'), file=sys.stderr)
print("AGENT_API_BASE_URL:", os.getenv('AGENT_API_BASE_URL', 'not set'), file=sys.stderr)
LMS_API_KEY = os.getenv('LMS_API_KEY')
if not LMS_API_KEY:
    print("Error: Missing LMS_API_KEY in environment", file=sys.stderr)
    sys.exit(1)
AGENT_API_BASE_URL = os.getenv('AGENT_API_BASE_URL', 'http://localhost:42002')
REQUIRED_VARS = ['LLM_API_KEY', 'LLM_API_BASE', 'LLM_MODEL']
config = {
    'api_key': os.getenv('LLM_API_KEY'),
    'api_base': os.getenv('LLM_API_BASE'),
    'model': os.getenv('LLM_MODEL')
}
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
def query_api(method, path, body=None):
    """Call the backend API"""
    url = f"{AGENT_API_BASE_URL.rstrip('/')}{path}"
    headers = {
        "Authorization": f"Bearer {LMS_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, 
                                   json=json.loads(body) if body else None, 
                                   timeout=10)
        else:
            return f"Error: Unsupported method {method}"
        return json.dumps({
            "status_code": response.status_code,
            "body": response.text
        })
    except Exception as e:
        return json.dumps({
            "status_code": 500,
            "body": f"Error: {str(e)}"
        })
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
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Query the backend API. Use for system data like item counts, scores, or to check API endpoints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST"],
                        "description": "HTTP method"
                    },
                    "path": {
                        "type": "string",
                        "description": "API path, e.g., /items/ or /analytics/scores?lab=lab-01"
                    },
                    "body": {
                        "type": "string",
                        "description": "JSON body for POST requests (optional)"
                    }
                },
                "required": ["method", "path"]
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
    elif name == 'query_api':
        result = query_api(
            args['method'],
            args['path'],
            args.get('body')
        )
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
    "You are a system assistant. Answer questions using:\n"
    "1. Wiki documentation - use read_file/list_files\n"
    "2. Source code - use read_file on backend/*.py\n"
    "3. System data - use query_api to get live data\n\n"
    "For static facts (framework, ports) check source code.\n"
    "For dynamic data (item counts, scores) use query_api.\n"
    "If query_api returns an error, read the error and debug."
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
