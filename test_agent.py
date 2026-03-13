import subprocess
import json


def test_agent_basic():
    """Test that agent.py returns valid JSON with required fields"""
    # Run agent with a simple question
    result = subprocess.run(
        ['uv', 'run', 'agent.py', 'What is 2+2?'],
        capture_output=True,
        text=True
    )
    # Check exit code
    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    # Parse JSON from stdout
    output = json.loads(result.stdout)
    # Check required fields exist
    assert 'answer' in output
    assert 'tool_calls' in output
    # Check tool_calls is an array
    assert isinstance(output['tool_calls'], list)
    # Check answer is not empty
    assert output['answer']
