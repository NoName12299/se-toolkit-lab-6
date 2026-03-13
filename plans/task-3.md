# Task 3: The System Agent - Implementation Plan

## Tool Schema Design
- **query_api**: HTTP client tool for backend API calls
- **Parameters**:
  - `method`: string (GET/POST)
  - `path`: string (API endpoint, e.g., "/items/")
  - `body`: optional string (JSON for POST requests)
- **Returns**: JSON with `status_code` and `body`

## Authentication
- Read `LMS_API_KEY` from environment variables
- Use `Authorization: Bearer` header
- Read `AGENT_API_BASE_URL` from env (default: http://localhost:42002)

## System Prompt Updates
- Teach LLM to choose between:
  - `read_file`/`list_files` for wiki and source code
  - `query_api` for live system data
- Include examples of when to use each tool

## Initial Benchmark Results
Date: 2026-03-14
Initial score: _/10
First failures:
Question X - failed because...
Question Y - failed because...


## Iteration Strategy
1. Fix one failing question at a time using `run_eval.py --index N`
2. For each failure:
   - Check if tool was called correctly
   - Verify tool implementation
   - Improve tool descriptions if LLM chooses wrong tool
   - Update system prompt for clarity
3. Re-run full benchmark after each fix
