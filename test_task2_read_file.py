import subprocess
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
def test_task2_read_file():
    """Task 2: Agent uses read_file for merge conflict question"""
    result = subprocess.run(
        ['uv', 'run', 'agent.py', 'How do you resolve a merge conflict?'],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert 'tool_calls' in output
    assert len(output['tool_calls']) > 0
    assert any(tc['tool'] == 'read_file' for tc in output['tool_calls'])
    assert 'git-workflow.md' in output.get('source', '')
