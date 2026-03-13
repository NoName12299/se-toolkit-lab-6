# Agent - Task 1

## LLM Provider
- **Provider**: Qwen Code API (self-hosted on VM)
- **Model**: `qwen3-coder-plus`
- **API Base**: `http://<vm-ip>:42005/v1`

## How it works
1. Reads config from `.env.agent.secret`
2. Takes question as command-line argument
3. Calls Qwen API on VM
4. Outputs JSON with `answer` and `tool_calls` (empty array)

## Usage
```bash
# Setup
cp .env.agent.example .env.agent.secret
# Edit .env.agent.secret with your VM IP and API key

# Run
uv run agent.py "Your question here"
