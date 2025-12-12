from noten import parse, ChordParser

def test_chord_with_parentheses():
    """Test parsing chords with parentheses like Bm(maj7)."""
    input_text = "| Bm(maj7) C(add9) |"
    ast = parse(input_text)

    measure = ast.body[0].measures[0]
    beats = measure.beats

    assert len(beats) == 2
    assert beats[0].root == "B"
    assert beats[0].quality == "m(maj7)"
    assert beats[1].root == "C"
    assert beats[1].quality == "(add9)"

def test_tuplet_with_parens_in_chords():
    """Test tuplet containing chords with parentheses."""
    input_text = "| (C(add9) G) |"
    ast = parse(input_text)

    measure = ast.body[0].measures[0]
    beats = measure.beats

    assert len(beats) == 1
    assert beats[0].type == "Tuplet"
    assert len(beats[0].chords) == 2
    assert beats[0].chords[0].root == "C"
    assert beats[0].chords[0].quality == "(add9)"
    assert beats[0].chords[1].root == "G"

def test_chord_parentheses_with_extensions():
    """Test chords with parentheses followed by other characters."""
    input_text = "| Bm(maj7)#5 |"
    ast = parse(input_text)

    measure = ast.body[0].measures[0]
    beats = measure.beats

    assert len(beats) == 1
    assert beats[0].root == "B"
    assert beats[0].quality == "m(maj7)#5"
