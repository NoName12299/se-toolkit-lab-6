import subprocess
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
def test_task3_query_api_for_data():
    """Task 3: Agent uses query_api for data question"""
    result = subprocess.run(
        ['uv', 'run', 'agent.py', 'How many items are in the database?'],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert 'tool_calls' in output
    assert any(
        tc['tool'] == 'query_api' and tc['args'].get('path') == '/items/'
        for tc in output['tool_calls']
    )
