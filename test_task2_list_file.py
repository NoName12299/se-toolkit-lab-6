import subprocess
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
def test_task2_list_files():
    """Task 2: Agent uses list_files for wiki listing question"""
    result = subprocess.run(
        ['uv', 'run', 'agent.py', 'What files are in the wiki?'],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert 'tool_calls' in output
    assert len(output['tool_calls']) > 0
    assert any(
        tc['tool'] == 'list_files' and tc['args'].get('path') == 'wiki'
        for tc in output['tool_calls']
    )
