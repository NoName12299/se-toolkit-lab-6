# Task 1: Call an LLM from Code - Implementation Plan

## LLM Provider Choice
- Provider: Qwen Code API (deployed on VM)
- Model: qwen3-coder-plus
- API Base: http://<vm-ip>:42005/v1

## Implementation Approach
1. Load configuration from .env.agent.secret
2. Accept question as command-line argument
3. Make HTTP request to LLM API
4. Parse response and extract answer
5. Output JSON with required fields
6. All debug output goes to stderr

## Dependencies
- requests: HTTP client
- python-dotenv: load environment variables
