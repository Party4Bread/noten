"""
Test suite for the Noten parser.
"""

import json
from noten import parse, ChordParser, calculate_durations


def test_chord_parser():
    """Test chord parsing into root, quality, bass components."""
    print("Testing Chord Parser")
    print("-" * 60)

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

    passed = 0
    failed = 0

    for chord_str, expected in test_cases:
        chord = ChordParser.parse(chord_str)
        result = {
            "root": chord.root,
            "quality": chord.quality,
            "bass": chord.bass
        }

        if result == expected:
            print(f"✓ {chord_str:<15} -> {result}")
            passed += 1
        else:
            print(f"✗ {chord_str:<15} -> {result} (expected {expected})")
            failed += 1

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return failed == 0


def test_basic_parsing():
    """Test basic parsing functionality."""
    print("\nTesting Basic Parsing")
    print("-" * 60)

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

    print("✓ Basic parsing test passed")
    return True


def test_tuplet_parsing():
    """Test tuplet parsing."""
    print("\nTesting Tuplet Parsing")
    print("-" * 60)

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

    print("✓ Tuplet parsing test passed")
    return True


def test_repeat_section():
    """Test repeat section parsing."""
    print("\nTesting Repeat Section Parsing")
    print("-" * 60)

    input_text = "|: G | C :| x3"

    ast = parse(input_text)
    ast_dict = ast.to_dict()

    measure_line = ast_dict['body'][0]
    repeat_section = measure_line['measures'][0]

    assert repeat_section['type'] == 'RepeatSection'
    assert repeat_section['repeatCount'] == 3
    assert len(repeat_section['measures']) == 2

    print("✓ Repeat section parsing test passed")
    return True


def test_continuation_rhythm():
    """Test rhythm calculation with continuation markers."""
    print("\nTesting Continuation Rhythm Calculation")
    print("-" * 60)

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

    print(f"✓ C gets {events[0]['duration']} beats, G gets {events[1]['duration']} beat")
    print("✓ Continuation rhythm test passed")
    return True


def test_tuplet_rhythm():
    """Test rhythm calculation for tuplets."""
    print("\nTesting Tuplet Rhythm Calculation")
    print("-" * 60)

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

    print("✓ C gets 2 beats, tuplet chords each get 2/3 beat")
    print("✓ Tuplet rhythm test passed")
    return True


def test_slash_chords():
    """Test slash chord parsing."""
    print("\nTesting Slash Chord Parsing")
    print("-" * 60)

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

    print("✓ G/B parsed correctly")
    print("✓ Am7/G parsed correctly")
    print("✓ Slash chord test passed")
    return True


def test_different_time_signatures():
    """Test rhythm calculation with different time signatures."""
    print("\nTesting Different Time Signatures")
    print("-" * 60)

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

    print("✓ 3/4 time: 3 chords each get 1 beat")

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

    print("✓ 6/8 time: C gets 3 beats, G gets 3 beats")
    print("✓ Time signature test passed")
    return True


def test_no_chord():
    """Test N.C. (no chord) parsing."""
    print("\nTesting N.C. (No Chord) Parsing")
    print("-" * 60)

    input_text = "| C . N.C. . |"

    ast = parse(input_text)
    ast_dict = ast.to_dict()

    beats = ast_dict['body'][0]['measures'][0]['beats']

    assert beats[0]['type'] == 'Chord'
    assert beats[0]['root'] == 'C'

    assert beats[2]['type'] == 'Chord'
    assert beats[2]['root'] == 'N.C.'

    print("✓ N.C. parsed as special chord")
    print("✓ No chord test passed")
    return True


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("NOTEN PARSER TEST SUITE")
    print("=" * 60)

    tests = [
        test_chord_parser,
        test_basic_parsing,
        test_tuplet_parsing,
        test_repeat_section,
        test_continuation_rhythm,
        test_tuplet_rhythm,
        test_slash_chords,
        test_different_time_signatures,
        test_no_chord,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"TOTAL: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
