# Agent - Task 2: Documentation Agent

## LLM Provider
- **Provider**: Qwen Code API (self-hosted on VM)
- **Model**: `qwen3-coder-plus`
- **API Base**: `http://10.93.26.62:42005/v1`

## Tools
### `read_file(path)`
- Reads file content from project repository
- Returns: file contents or error message
- Security: prevents path traversal (../)

### `list_files(path)`
- Lists files and directories at given path
- Returns: newline-separated listing

## Agentic Loop
1. Send question + tool definitions to LLM
2. If LLM returns `tool_calls` → execute tools, append results, repeat
3. If LLM returns text → final answer (with source)
4. Max 10 tool calls per question

## Output Format
```json
{
  "answer": "LLM response text",
  "source": "wiki/file.md#section",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "..."}
  ]
}
