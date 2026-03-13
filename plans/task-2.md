# Task 2: The Documentation Agent - Implementation Plan

## 1. Tool Schemas Definition
- Define `read_file` tool schema:
  - Parameters: `path` (string) - relative path from project root
  - Returns: file contents or error message
- Define `list_files` tool schema:
  - Parameters: `path` (string) - relative directory path
  - Returns: newline-separated listing of entries
- Register both schemas in OpenRouter API request under `tools` field

## 2. Agentic Loop Implementation
while tool_calls_count < 10:
response = call_llm_with_tools(messages, tool_schemas)

if response has tool_calls:
for each tool_call:
execute_tool(tool_call)
append_result_as_tool_message()
tool_calls_count++
else:

LLM returned final answer
extract_answer_and_source()
break
- Track all tool calls with their args and results
- Stop after 10 tool calls max

## 3. Path Security
- Resolve absolute path: `os.path.abspath(os.path.join(project_root, path))`
- Check if resolved path starts with `project_root`
- Reject paths containing `..` or trying to escape project directory
- Return error message for invalid paths

## 4. Output Format
```json
{
  "answer": "string",
  "source": "wiki/file.md#section",
  "tool_calls": [
    {"tool": "read_file", "args": {"path": "..."}, "result": "..."}
  ]
}
