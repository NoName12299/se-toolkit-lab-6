import subprocess
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
def test_task3_read_file_for_framework():
    """Task 3: Agent uses read_file for static system question"""
    result = subprocess.run(
        ['uv', 'run', 'agent.py', 'What framework does the backend use?'],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert 'tool_calls' in output
    assert any(tc['tool'] == 'read_file' for tc in output['tool_calls'])
