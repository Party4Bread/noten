"""
Comprehensive tests to improve coverage for noten package.
"""

import pytest
from fractions import Fraction
from noten.noten_lexer import Token, TokenType, NotenLexer, tokenize
from noten.noten_parser import (
    ChordNode, ContinuationNode, TupletNode, MeasureNode,
    RepeatMeasureNode, RepeatSectionNode, MeasureLineNode,
    AnnotationNode, SongNode, ChordParser, NotenParser, parse
)
from noten.noten_rhythm import (
    TimeSignature, RhythmCalculator, calculate_durations, print_rhythm_analysis
)

# --- Lexer Tests ---

def test_token_repr():
    token = Token(TokenType.CHORD, "C", 1, 1)
    assert repr(token) == "Token(CHORD, 'C', line=1, col=1)"

def test_lexer_unexpected_character():
    with pytest.raises(ValueError, match="Unexpected character"):
        tokenize("Invalid @ Character")

def test_lexer_get_tokens_include_whitespace():
    tokens = tokenize("C D", include_whitespace=True)
    assert any(t.type == TokenType.WHITESPACE for t in tokens)

    tokens_no_ws = tokenize("C D", include_whitespace=False)
    assert not any(t.type == TokenType.WHITESPACE for t in tokens_no_ws)

# --- Parser Tests ---

def test_chord_node_to_dict():
    node = ChordNode(root="C", quality="maj7", bass="G")
    assert node.to_dict() == {
        "type": "Chord",
        "root": "C",
        "quality": "maj7",
        "bass": "G"
    }

def test_continuation_node_to_dict():
    node = ContinuationNode()
    assert node.to_dict() == {"type": "Continuation"}

def test_tuplet_node_to_dict():
    chord = ChordNode(root="C")
    node = TupletNode(chords=[chord])
    assert node.to_dict() == {
        "type": "Tuplet",
        "chords": [{"type": "Chord", "root": "C", "quality": "", "bass": None}]
    }

def test_measure_node_to_dict():
    chord = ChordNode(root="C")
    node = MeasureNode(beats=[chord])
    assert node.to_dict() == {
        "type": "Measure",
        "beats": [{"type": "Chord", "root": "C", "quality": "", "bass": None}]
    }

def test_repeat_measure_node_to_dict():
    node = RepeatMeasureNode(count=2)
    assert node.to_dict() == {
        "type": "RepeatMeasure",
        "count": 2
    }

def test_repeat_section_node_to_dict():
    measure = MeasureNode()
    node = RepeatSectionNode(measures=[measure], repeat_count=3)
    assert node.to_dict() == {
        "type": "RepeatSection",
        "repeatCount": 3,
        "measures": [{"type": "Measure", "beats": []}]
    }

def test_measure_line_node_to_dict():
    measure = MeasureNode()
    node = MeasureLineNode(measures=[measure])
    assert node.to_dict() == {
        "type": "MeasureLine",
        "measures": [{"type": "Measure", "beats": []}]
    }

def test_annotation_node_to_dict():
    node = AnnotationNode(content="key: C")
    assert node.to_dict() == {
        "type": "Annotation",
        "content": "key: C"
    }

def test_song_node_to_dict():
    anno = AnnotationNode(content="key: C")
    node = SongNode(body=[anno])
    assert node.to_dict() == {
        "type": "Song",
        "body": [{"type": "Annotation", "content": "key: C"}]
    }

def test_chord_parser_invalid():
    with pytest.raises(ValueError, match="Invalid chord"):
        ChordParser.parse("Hmaj7")

def test_parser_unexpected_token():
    # Construct a token list that defies the grammar (e.g. starting with REPEAT_END)
    tokens = [Token(TokenType.REPEAT_END, ":|", 1, 1)]
    parser = NotenParser(tokens)
    with pytest.raises(ValueError, match="Unexpected token"):
        parser.parse()

def test_parser_expected_token_error():
    # Expecting ANNOTATION_CONTENT after ANNOTATION_START
    tokens = [
        Token(TokenType.ANNOTATION_START, "{", 1, 1),
        Token(TokenType.ANNOTATION_END, "}", 1, 2)
    ]
    parser = NotenParser(tokens)
    with pytest.raises(ValueError, match="Expected annotation content"):
        parser.parse()

def test_parser_incomplete_measure():
    # Measure start without end
    tokens = [Token(TokenType.BAR_START, "|", 1, 1)]
    parser = NotenParser(tokens)
    with pytest.raises(ValueError, match="Expected closing '|'"):
        parser.parse()

def test_parser_tuplet_empty():
    # Empty tuplet ()
    tokens = [
        Token(TokenType.BAR_START, "|", 1, 1),
        Token(TokenType.TUPLET_START, "(", 1, 2),
        Token(TokenType.TUPLET_END, ")", 1, 3),
        Token(TokenType.BAR_START, "|", 1, 4)
    ]
    parser = NotenParser(tokens)
    # This should parse but result in empty tuplet
    song = parser.parse()
    measure = song.body[0].measures[0]
    tuplet = measure.beats[0]
    assert len(tuplet.chords) == 0

def test_parser_repeat_measure_with_count():
    # | %x2 |
    tokens = [
        Token(TokenType.BAR_START, "|", 1, 1),
        Token(TokenType.SINGLE_REPEAT, "%", 1, 2),
        Token(TokenType.MULTI_REPEAT, "x2", 1, 3),
        Token(TokenType.BAR_START, "|", 1, 5)
    ]
    parser = NotenParser(tokens)
    song = parser.parse()
    repeat_measure = song.body[0].measures[0]
    assert isinstance(repeat_measure, RepeatMeasureNode)
    assert repeat_measure.count == 2

def test_parser_multi_repeat_after_measure():
    # | C | x2
    text = "| C | x2"
    song = parse(text)
    measure = song.body[0].measures[0]
    # The parser currently attaches repeat_count to MeasureNode dynamically
    assert getattr(measure, 'repeat_count', 1) == 2

def test_parser_repeat_section_with_single_repeat():
    # |: % :|
    text = "|: % :|"
    song = parse(text)
    repeat_section = song.body[0].measures[0]
    assert len(repeat_section.measures) == 1
    assert isinstance(repeat_section.measures[0], RepeatMeasureNode)

def test_parser_break_in_loops():
    # Coverage for break statements in loops
    # | C % | with single repeat inside measure content (invalid generally but parser handles it by breaking)
    tokens = [
        Token(TokenType.BAR_START, "|", 1, 1),
        Token(TokenType.CHORD, "C", 1, 2),
        Token(TokenType.SINGLE_REPEAT, "%", 1, 3), # This triggers break in _parse_measure_content
        Token(TokenType.BAR_START, "|", 1, 4)
    ]
    parser = NotenParser(tokens)
    # The parser expects a closing bar or end of line/file, but gets % which breaks _parse_measure_content
    # and then _parse_measure checks for bar end. % is not bar end.
    with pytest.raises(ValueError, match="Expected closing '|'"):
        parser.parse()

# --- Rhythm Tests ---

def test_time_signature_init():
    ts = TimeSignature("3/4")
    assert ts.numerator == 3
    assert ts.denominator == 4
    assert str(ts) == "3/4"
    assert ts.beats_per_measure == Fraction(3, 1)

def test_time_signature_invalid():
    with pytest.raises(ValueError, match="Invalid time signature"):
        TimeSignature("4")

def test_rhythm_calculator_repeat_measure():
    # Test that RepeatMeasure returns empty list (as currently implemented)
    text = "| C | % |"
    ast = parse(text)
    calc = RhythmCalculator()
    events = calc.calculate_song_durations(ast.to_dict())
    # 1 chord event from first measure, 0 from repeat measure (current implementation)
    assert len(events) == 1

def test_rhythm_calculator_repeat_section():
    text = "|: C :| x2"
    ast = parse(text)
    events = calculate_durations(ast.to_dict())
    # C plays twice
    assert len(events) == 2
    assert events[0]['start'] == 0
    assert events[1]['start'] == 4

def test_rhythm_calculator_tuplet_empty():
    text = "| () |"
    ast = parse(text)
    events = calculate_durations(ast.to_dict())
    assert len(events) == 0

def test_print_rhythm_analysis(capsys):
    events = [
        {
            'chord': {'root': 'C', 'quality': 'maj7', 'bass': 'G'},
            'start': Fraction(0, 1),
            'duration': Fraction(4, 1),
            'in_tuplet': False
        },
        {
            'chord': {'root': 'N.C.', 'quality': '', 'bass': None},
            'start': Fraction(4, 1),
            'duration': Fraction(4, 1),
            'in_tuplet': True
        }
    ]
    print_rhythm_analysis(events)
    captured = capsys.readouterr()
    assert "Cmaj7/G" in captured.out
    assert "N.C." in captured.out
    assert "Yes" in captured.out # Tuplet marker

def test_parser_measure_line_edge_cases():
    # Case: | % | where closing bar logic is tricky
    text = "| % |"
    song = parse(text)
    assert isinstance(song.body[0].measures[0], RepeatMeasureNode)

def test_parser_measure_line_closing_bar_logic():
    # Case: | C | \n (Standard)
    tokens = [
        Token(TokenType.BAR_START, "|", 1, 1),
        Token(TokenType.CHORD, "C", 1, 2),
        Token(TokenType.BAR_START, "|", 1, 3),
        Token(TokenType.NEWLINE, "\n", 1, 4)
    ]
    parser = NotenParser(tokens)
    song = parser.parse()
    assert len(song.body[0].measures) == 1
