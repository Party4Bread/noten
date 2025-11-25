"""
Test suite for the Noten parser.
"""

import json
import pytest
from noten import parse, ChordParser, calculate_durations


def test_chord_parser():
    """Test chord parsing into root, quality, bass components."""

    test_cases = [
        ("C", {"root": "C", "quality": "", "bass": None}),
        ("Cmaj7", {"root": "C", "quality": "maj7", "bass": None}),
        ("Am", {"root": "A", "quality": "m", "bass": None}),
        ("Am7", {"root": "A", "quality": "m7", "bass": None}),
        ("G/B", {"root": "G", "quality": "", "bass": "B"}),
        ("Am7/G", {"root": "A", "quality": "m7", "bass": "G"}),
        ("Db", {"root": "Db", "quality": "", "bass": None}),
        ("F#m7b5", {"root": "F#", "quality": "m7b5", "bass": None}),
        ("N.C.", {"root": "N.C.", "quality": "", "bass": None}),
    ]

    for chord_str, expected in test_cases:
        chord = ChordParser.parse(chord_str)
        result = {
            "root": chord.root,
            "quality": chord.quality,
            "bass": chord.bass
        }
        assert result == expected, f"{chord_str} failed"


def test_basic_parsing():
    """Test basic parsing functionality."""
    input_text = """{title: Test Song}
{key: G}
{time: 4/4}

| G . C . | D . G . |
"""

    ast = parse(input_text)
    ast_dict = ast.to_dict()

    # Check song structure
    assert ast_dict['type'] == 'Song'
    assert len(ast_dict['body']) == 4  # 3 annotations + 1 measure line

    # Check annotations
    annotations = [n for n in ast_dict['body'] if n['type'] == 'Annotation']
    assert len(annotations) == 3
    assert annotations[0]['content'] == 'title: Test Song'
    assert annotations[1]['content'] == 'key: G'
    assert annotations[2]['content'] == 'time: 4/4'

    # Check measure line
    measure_lines = [n for n in ast_dict['body'] if n['type'] == 'MeasureLine']
    assert len(measure_lines) == 1
    assert len(measure_lines[0]['measures']) == 2


def test_tuplet_parsing():
    """Test tuplet parsing."""
    input_text = "| C (G F Em) D |"

    ast = parse(input_text)
    ast_dict = ast.to_dict()

    measure = ast_dict['body'][0]['measures'][0]
    beats = measure['beats']

    assert len(beats) == 3  # C, tuplet, D
    assert beats[0]['type'] == 'Chord'
    assert beats[1]['type'] == 'Tuplet'
    assert beats[2]['type'] == 'Chord'

    tuplet = beats[1]
    assert len(tuplet['chords']) == 3
    assert tuplet['chords'][0]['root'] == 'G'
    assert tuplet['chords'][1]['root'] == 'F'
    assert tuplet['chords'][2]['root'] == 'E'
    assert tuplet['chords'][2]['quality'] == 'm'


def test_repeat_section():
    """Test repeat section parsing."""
    input_text = "|: G | C :| x3"

    ast = parse(input_text)
    ast_dict = ast.to_dict()

    measure_line = ast_dict['body'][0]
    repeat_section = measure_line['measures'][0]

    assert repeat_section['type'] == 'RepeatSection'
    assert repeat_section['repeatCount'] == 3
    assert len(repeat_section['measures']) == 2


def test_continuation_rhythm():
    """Test rhythm calculation with continuation markers."""
    # Example from spec: | C . . G | has Cmaj7 for 3 beats, G for 1 beat
    input_text = """{time: 4/4}
| C . . G |
"""

    ast = parse(input_text)
    events = calculate_durations(ast.to_dict())

    assert len(events) == 2
    assert events[0]['chord']['root'] == 'C'
    assert float(events[0]['duration']) == 3.0
    assert events[1]['chord']['root'] == 'G'
    assert float(events[1]['duration']) == 1.0


def test_tuplet_rhythm():
    """Test rhythm calculation for tuplets."""
    # Example from spec: | C (G F G) | - two top-level elements
    input_text = """{time: 4/4}
| C (G F G) |
"""

    ast = parse(input_text)
    events = calculate_durations(ast.to_dict())

    assert len(events) == 4  # C + 3 chords in tuplet

    # C gets 2 beats
    assert events[0]['chord']['root'] == 'C'
    assert abs(float(events[0]['duration']) - 2.0) < 0.001

    # Each chord in tuplet gets 2/3 beat
    for i in range(1, 4):
        assert abs(float(events[i]['duration']) - (2.0 / 3.0)) < 0.001


def test_slash_chords():
    """Test slash chord parsing."""
    input_text = "| G/B | Am7/G | C |"

    ast = parse(input_text)
    ast_dict = ast.to_dict()

    beats = ast_dict['body'][0]['measures'][0]['beats']

    # G/B
    assert beats[0]['root'] == 'G'
    assert beats[0]['bass'] == 'B'

    # Am7/G
    measure2_beats = ast_dict['body'][0]['measures'][1]['beats']
    assert measure2_beats[0]['root'] == 'A'
    assert measure2_beats[0]['quality'] == 'm7'
    assert measure2_beats[0]['bass'] == 'G'


def test_different_time_signatures():
    """Test rhythm calculation with different time signatures."""
    # 3/4 time
    input_text = """{time: 3/4}
| C G Am |
"""

    ast = parse(input_text)
    events = calculate_durations(ast.to_dict())

    # Each chord should get 1 beat (3 beats / 3 chords)
    assert len(events) == 3
    for event in events:
        assert float(event['duration']) == 1.0

    # 6/8 time
    input_text2 = """{time: 6/8}
| C . G . |
"""

    ast2 = parse(input_text2)
    events2 = calculate_durations(ast2.to_dict())

    # 2 top-level elements (C ., G .)
    # Each gets 3 beats, continuation extends the chord
    assert len(events2) == 2
    assert float(events2[0]['duration']) == 3.0
    assert float(events2[1]['duration']) == 3.0


def test_no_chord():
    """Test N.C. (no chord) parsing."""
    input_text = "| C . N.C. . |"

    ast = parse(input_text)
    ast_dict = ast.to_dict()

    beats = ast_dict['body'][0]['measures'][0]['beats']

    assert beats[0]['type'] == 'Chord'
    assert beats[0]['root'] == 'C'

    assert beats[2]['type'] == 'Chord'
    assert beats[2]['root'] == 'N.C.'
