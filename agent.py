#!/usr/bin/env python
"""
agent.py - CLI tool that calls Qwen LLM on VM and returns JSON response.
Task 1: Call an LLM from Code
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
import argparse


def load_config():
    """Load configuration from .env.agent.secret"""
    # Load environment variables from .env.agent.secret
    load_dotenv('.env.agent.secret')
    required_vars = ['LLM_API_KEY', 'LLM_API_BASE', 'LLM_MODEL']
    config = {}
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        config[var.lower()] = value
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}", 
              file=sys.stderr)
        print("Please create .env.agent.secret with:", file=sys.stderr)
        print("LLM_API_KEY=my-secret-qwen-key", file=sys.stderr)
        print("LLM_API_BASE=http://<your-vm-ip>:42005/v1", file=sys.stderr)
        print("LLM_MODEL=qwen3-coder-plus", file=sys.stderr)
        sys.exit(1)
    return config
def call_qwen(question: str, config: dict) -> dict:
    """
    Call Qwen API on VM and return the response.
    Args:
        question: User's question
        config: Configuration with api_key, api_base, model
    Returns:
        Dict with 'answer' and 'tool_calls'
    """
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config['model'],
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    # Build API URL (Qwen уже имеет /v1 в базовом URL)
    api_base = config['api_base'].rstrip('/')
    url = f"{api_base}/chat/completions"
    # Print debug info to stderr (not stdout!)
    print(f"Calling Qwen on VM at: {url}", file=sys.stderr)
    print(f"Model: {config['model']}", file=sys.stderr)
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Извлекаем ответ из Qwen (OpenAI-совместимый формат)
        answer = data['choices'][0]['message']['content']
        # Для Task 1 tool_calls всегда пустой массив
        return {
            "answer": answer.strip(),
            "tool_calls": []
        }
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to Qwen at {url}", file=sys.stderr)
        print("Make sure:", file=sys.stderr)
        print("1. Qwen container is running on VM", file=sys.stderr)
        print("2. VM IP is correct in .env.agent.secret", file=sys.stderr)
        print("3. Port 42005 is open", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error calling Qwen API: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing Qwen response: {e}", file=sys.stderr)
        print(f"Raw response: {response.text if 'response' in locals() else 'N/A'}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Call Qwen LLM on VM with a question')
    parser.add_argument('question', help='Question to ask the LLM')
    args = parser.parse_args()
    # Load configuration
    config = load_config()
    # Call Qwen
    result = call_qwen(args.question, config)
    # Output only JSON to stdout (all debug goes to stderr)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
