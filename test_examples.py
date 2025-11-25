"""
Test all example noten files to ensure they parse correctly.
"""

import os
import pytest
from noten import parse, calculate_durations

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), 'examples')
EXAMPLE_FILES = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith('.noten')] if os.path.exists(EXAMPLES_DIR) else []

@pytest.mark.parametrize("filename", EXAMPLE_FILES)
def test_example_file(filename):
    """
    Test parsing and rhythm analysis for an example file.
    """
    filepath = os.path.join(EXAMPLES_DIR, filename)
    print(f"\nTesting: {filename}")

    # Read file
    with open(filepath, 'r') as f:
        content = f.read()

    # Parse
    ast = parse(content)
    ast_dict = ast.to_dict()

    # Basic structure checks
    assert ast_dict['type'] == 'Song'
    assert 'body' in ast_dict
    assert len(ast_dict['body']) > 0

    # Calculate rhythm
    events = calculate_durations(ast_dict)
    assert len(events) > 0

    # Verify events structure
    for event in events:
        assert 'start' in event
        assert 'duration' in event
        assert 'chord' in event
