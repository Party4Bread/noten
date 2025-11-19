# Noten: LLM-Parseable Chord Progression Format

A token-efficient, unambiguous text-based musical chord notation system designed for seamless integration with Large Language Models.

## Overview

**Noten** (also known as LLM-Chart) is a chord progression format that balances three key requirements:
- **Unambiguous**: Clear rhythm alignment eliminates guesswork
- **Token-Efficient**: Concise syntax minimizes LLM context usage
- **Human-Readable**: Intuitive for musicians to read and write

## Quick Start

### Installation

The noten package is now properly packaged and can be installed with `uv` (recommended) or `pip`:

```bash
# Install with uv (recommended - fast!)
uv pip install -e .

# Or with traditional pip
pip install -e .
```

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

```bash
# Run tests
python test_noten.py

# Run demos
python demo_reharmonization.py
python demo_real_llm.py  # Requires API keys
```

### Basic Example

```
{title: My Song}
{key: C}
{time: 4/4}

{Verse}
| C . . G | Am . F . |

{Chorus}
|: C . Am . | F . G . :| x2
```

## Format Specification

### Annotations

Metadata and structural labels in curly braces:
```
{title: Song Name}
{key: C}
{time: 4/4}
{Verse 1}
```

### Measures

Chord content between bar lines `| ... |`:
```
| C G Am F |          # Four chords, one beat each (in 4/4)
| C . . G |            # C for 3 beats, G for 1 beat
| C . G . |            # C for 2 beats, G for 2 beats
```

### Continuation Marker (`.`)

Extends the previous chord's duration:
```
| C . . . |            # C for 4 beats
| C . G . |            # C for 2 beats, G for 2 beats
```

### Tuplets

Group chords within a beat using parentheses:
```
| C (G F Em) |         # C for 2 beats, then triplet (G F Em) for 2 beats
```

### Repeat Sections

```
|: C | G :| x3         # Repeat 3 times total
% | Am |               # Repeat previous measure, then Am
```

### Chord Syntax

```
C                      # Root: C, Quality: (major)
Am                     # Root: A, Quality: m (minor)
Cmaj7                  # Root: C, Quality: maj7
G/B                    # Root: G, Bass: B (slash chord)
Am7/G                  # Root: A, Quality: m7, Bass: G
N.C.                   # No chord
```

## Python API

### Parsing

```python
from noten import parse

ast = parse(noten_string)
ast_dict = ast.to_dict()  # Convert to dictionary
```

### Rhythm Analysis

```python
from noten import calculate_durations

events = calculate_durations(ast_dict)
# Returns list of chord events with start time and duration
```

### Example

```python
from noten import parse, calculate_durations, print_rhythm_analysis

noten = """
{time: 4/4}
| C . . G | (Am G F) C |
"""

ast = parse(noten)
events = calculate_durations(ast.to_dict())
print_rhythm_analysis(events)
```

Output:
```
Time       Duration     Chord           Tuplet
------------------------------------------------------------
0.00       3.000        C
3.00       1.000        G
4.00       0.667        Am              Yes
4.67       0.667        G               Yes
5.33       0.667        F               Yes
6.00       2.000        C
```

## LLM Integration

### Chord Reharmonization Demo

```bash
python demo_reharmonization.py
```

This demonstrates:
1. Parsing original chord progression
2. Sending to LLM with reharmonization prompt
3. Parsing LLM's noten output
4. Comparing original vs. reharmonized versions

### LLM Integration Example

```python
import anthropic

def reharmonize_with_claude(noten_input):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Reharmonize this chord progression with jazz chords:

{noten_input}

Output in the same noten format."""

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
```

## Specification Issues

See [SPEC_ISSUES.md](SPEC_ISSUES.md) for detailed analysis of logical flaws found in the original specification and their proposed fixes.

### Key Fixes Implemented

1. **Chord Parsing**: Correctly splits chords into root/quality/bass
   - ✗ Wrong: `Am` → `root="Am", quality=""`
   - ✓ Correct: `Am` → `root="A", quality="m"`

2. **Repeat Semantics**: `x3` means play 3 times total (not 3 additional)

3. **Slash Chords**: `G/B` → `root="G", bass="B"`

4. **Shared Bar Lines**: `| A | B |` middle `|` correctly handled

## File Structure

```
noten/
├── pyproject.toml               # Package metadata and dependencies
├── README.md                    # This file
├── INSTALLATION.md              # Installation guide
├── noten_desc.md                # Original specification
├── src/
│   └── noten/                  # Main package
│       ├── __init__.py         # Package exports
│       ├── noten_lexer.py      # Tokenizer
│       ├── noten_parser.py     # Parser & AST
│       └── noten_rhythm.py     # Rhythm calculation
├── test_noten.py               # Test suite
├── test_examples.py            # Example file tests
├── demo_reharmonization.py     # Simulated LLM demo
└── demo_real_llm.py            # Real LLM API demo
```

## Running Tests

```bash
python test_noten.py
```

Tests cover:
- ✓ Chord parsing (root/quality/bass splitting)
- ✓ Basic measure parsing
- ✓ Tuplet parsing
- ✓ Repeat sections
- ✓ Continuation rhythm calculation
- ✓ Tuplet rhythm calculation
- ✓ Slash chords
- ✓ Different time signatures
- ✓ N.C. (no chord) handling

## Use Cases

### Music Theory Education
```python
# Analyze chord progressions
ast = parse(progression)
events = calculate_durations(ast.to_dict())
# Visualize rhythm, identify patterns
```

### AI Music Generation
```python
# LLM generates chord progressions
prompt = "Generate a jazz progression in C"
noten_output = llm.generate(prompt)
ast = parse(noten_output)
```

### Style Transfer
```python
# Convert pop → jazz
prompt = f"Reharmonize as jazz: {pop_progression}"
jazz_progression = llm.generate(prompt)
```

### Automatic Accompaniment
```python
# Generate bass/piano parts from chords
chords = parse(noten_input)
bass_line = generate_bass_from_chords(chords)
```

## Design Principles

### 1. Unambiguous Rhythm
Unlike traditional lead sheets where rhythm is ambiguous, noten uses:
- Equal beat division among elements
- Explicit continuation markers (`.`)
- Tuplets for subdivisions

### 2. Token Efficiency
- Concise syntax: `| C . G . |` vs verbose formats
- Minimal punctuation
- Reuses `|` for bar start/end

### 3. Human Readability
- Familiar chord symbols (C, Am7, G/B)
- Natural bar line notation
- Intuitive continuation dots

### 4. Structural Agnostic
- Free-form annotations `{...}` instead of rigid sections
- Flexible metadata
- No enforced song structure

## Advantages Over Other Formats

### vs. ChordPro
- ✓ Unambiguous rhythm (ChordPro doesn't specify timing)
- ✓ More concise tuplet syntax
- ✓ Better LLM compatibility

### vs. MusicXML
- ✓ 1000x more token-efficient
- ✓ Human-readable
- ✓ Easier for LLMs to generate

### vs. ABC Notation
- ✓ Focuses on harmony, not melody
- ✓ Simpler syntax for chord progressions
- ✓ Better chord quality representation

## Future Enhancements

Potential additions to the format:
- Dynamics annotations: `{dynamics: mf}`
- Tempo changes: `{tempo: 120}`
- Section links: `{repeat: Verse 1}`
- Chord voicings: `Cmaj7<3,5,7,9>` (optional)
- MIDI export functionality

## Contributing

This is a research/demo project. Feedback welcome on:
- Specification clarity
- Parser edge cases
- LLM integration patterns
- Additional use cases

## License

MIT License - See implementation files for details.

## References

- Original specification: `noten_desc.md`
- Specification issues: `SPEC_ISSUES.md`
- Demo: `demo_reharmonization.py`

---

**Created as a demonstration of LLM-friendly musical notation.**
