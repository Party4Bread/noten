"""
Noten LLM Demo: Chord Reharmonization

This demo showcases the noten format being used with an LLM for chord reharmonization tasks.
The LLM can parse noten input and generate noten output, making it ideal for musical AI applications.
"""

import os
import json
from typing import Optional, Dict, Any
from noten import parse, calculate_durations, print_rhythm_analysis


# Simulated LLM response for demo purposes
SIMULATED_REHARMONIZATION = """{title: Reharmonized Version}
{key: C}
{time: 4/4}
{style: Jazz Reharmonization}

{Intro}
| Cmaj9 . . G13 | (Am9 Dm7 G7alt) Cmaj7 |
|: Fmaj7#11 | Em7 A7b9 :| x2
"""


def create_reharmonization_prompt(noten_input: str) -> str:
    """
    Create a prompt for LLM chord reharmonization.

    Args:
        noten_input: Original chord progression in noten format

    Returns:
        Formatted prompt for the LLM
    """
    prompt = f"""You are a jazz harmonization expert. I will provide a chord progression in the "noten" format (LLM-Chart), and you should reharmonize it with more sophisticated jazz chords while maintaining the same structure and rhythm.

NOTEN FORMAT RULES:
- Annotations: {{key: C}}, {{time: 4/4}}, {{title: Song Name}}
- Measures: | C . . G | (bar lines with chords/continuations)
- Continuation: . extends the previous chord
- Tuplets: (Am G F) groups chords within a beat
- Repeats: |: C | D :| x2 (repeat section)
- Single repeat: % (repeat previous measure)

ORIGINAL PROGRESSION:
{noten_input}

Please provide a jazz reharmonization using:
- Extended chords (maj7, 9, 11, 13)
- Altered dominants (7alt, 7b9, 7#9)
- Substitute chords where appropriate
- Maintain the same time signature and basic structure
- Output ONLY in noten format, starting with annotations

Your reharmonization:"""

    return prompt


def reharmonize_with_llm(noten_input: str, api_key: Optional[str] = None, use_simulation: bool = True) -> str:
    """
    Send chord progression to LLM for reharmonization.

    Args:
        noten_input: Original progression in noten format
        api_key: Optional API key for LLM service
        use_simulation: If True, use simulated response instead of real LLM

    Returns:
        Reharmonized progression in noten format
    """
    if use_simulation:
        print("Using simulated LLM response for demo...")
        return SIMULATED_REHARMONIZATION

    # Real LLM integration (requires API key)
    # This is a placeholder - you would implement actual API calls here
    print("Real LLM integration not implemented in this demo.")
    print("To use a real LLM, you would:")
    print("1. Install: pip install anthropic  # or openai")
    print("2. Set API key: export ANTHROPIC_API_KEY=your-key")
    print("3. Implement API call in this function")
    print("\nFalling back to simulated response...")
    return SIMULATED_REHARMONIZATION


def analyze_progression(noten_input: str, title: str = "Progression"):
    """
    Parse and analyze a noten progression.

    Args:
        noten_input: Chord progression in noten format
        title: Title for display

    Returns:
        Tuple containing the AST dictionary and the list of rhythm events, or (None, None) on failure.
    """
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}")
    print("\nNoten Input:")
    print(noten_input)

    # Parse the noten input
    try:
        ast = parse(noten_input)
        ast_dict = ast.to_dict()

        print("\n" + "-" * 70)
        print("Parsed Structure:")
        print("-" * 70)

        # Extract metadata
        annotations = [n for n in ast_dict['body'] if n['type'] == 'Annotation']
        for anno in annotations:
            print(f"  {anno['content']}")

        # Calculate rhythm
        events = calculate_durations(ast_dict)

        print("\n" + "-" * 70)
        print("Rhythm Analysis:")
        print("-" * 70)
        print()
        print_rhythm_analysis(events)

        # Calculate total duration
        if events:
            total_duration = max(e['start'] + e['duration'] for e in events)
            print(f"\nTotal duration: {float(total_duration)} beats")

        return ast_dict, events

    except Exception as e:
        print(f"\n✗ Error parsing noten input: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def compare_progressions(original_events, reharmonized_events):
    """
    Compare original and reharmonized progressions side-by-side.

    Args:
        original_events: List of rhythm events from the original progression.
        reharmonized_events: List of rhythm events from the reharmonized progression.
    """
    print(f"\n{'=' * 70}")
    print("COMPARISON")
    print(f"{'=' * 70}")

    print(f"\nOriginal: {len(original_events)} chord events")
    print(f"Reharmonized: {len(reharmonized_events)} chord events")

    print("\nSide-by-side comparison (first 10 events):")
    print(f"{'Time':<8} {'Original':<20} {'Reharmonized':<20}")
    print("-" * 60)

    for i in range(min(10, max(len(original_events), len(reharmonized_events)))):
        time_str = f"{float(original_events[i]['start']):.1f}" if i < len(original_events) else "-"

        if i < len(original_events):
            orig_chord = original_events[i]['chord']
            orig_str = f"{orig_chord['root']}{orig_chord['quality']}"
        else:
            orig_str = "-"

        if i < len(reharmonized_events):
            reh_chord = reharmonized_events[i]['chord']
            reh_str = f"{reh_chord['root']}{reh_chord['quality']}"
        else:
            reh_str = "-"

        print(f"{time_str:<8} {orig_str:<20} {reh_str:<20}")


def demo_reharmonization():
    """
    Run the complete reharmonization demo.

    This function executes the full pipeline:
    1. Parsing an example original progression.
    2. Generating a reharmonization prompt.
    3. Simulating an LLM response (or calling one if configured).
    4. Parsing the reharmonized result.
    5. Comparing both versions.
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         NOTEN LLM DEMO: CHORD REHARMONIZATION                   ║
║                                                                  ║
║  Demonstrating the noten format's ability to work seamlessly    ║
║  with Large Language Models for musical tasks.                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

    # Original progression (simple pop progression)
    original_progression = """{title: Simple Pop Song}
{key: C}
{time: 4/4}

{Verse}
| C . . G | Am . F . |
| C . G . | F . . . |

{Chorus}
|: C . Am . | F . G . :| x2
"""

    # Step 1: Analyze original
    print("\nSTEP 1: Analyzing Original Progression")
    original_ast, original_events = analyze_progression(
        original_progression,
        title="ORIGINAL PROGRESSION"
    )

    if not original_ast:
        print("Failed to parse original progression. Exiting.")
        return

    # Step 2: Generate prompt
    print("\n" + "=" * 70)
    print("STEP 2: Generating LLM Prompt")
    print("=" * 70)
    prompt = create_reharmonization_prompt(original_progression)
    print("\nPrompt preview (first 500 chars):")
    print(prompt[:500] + "...")

    # Step 3: Get reharmonization from LLM
    print("\n" + "=" * 70)
    print("STEP 3: Getting Reharmonization from LLM")
    print("=" * 70)
    reharmonized = reharmonize_with_llm(original_progression, use_simulation=True)

    # Step 4: Analyze reharmonization
    print("\n" + "=" * 70)
    print("STEP 4: Analyzing Reharmonized Progression")
    print("=" * 70)
    reharmonized_ast, reharmonized_events = analyze_progression(
        reharmonized,
        title="REHARMONIZED PROGRESSION"
    )

    if not reharmonized_ast:
        print("Failed to parse reharmonized progression.")
        return

    # Step 5: Compare
    compare_progressions(original_events, reharmonized_events)

    # Step 6: Summary
    print(f"\n{'=' * 70}")
    print("DEMO SUMMARY")
    print(f"{'=' * 70}")
    print("\n✓ Successfully demonstrated noten format with LLM")
    print("✓ Original progression parsed and analyzed")
    print("✓ LLM reharmonization generated in noten format")
    print("✓ Reharmonized progression parsed and analyzed")
    print("✓ Both progressions compared side-by-side")

    print("\nKey Benefits of Noten Format for LLM Integration:")
    print("  1. UNAMBIGUOUS: Clear rhythm alignment with continuations and tuplets")
    print("  2. TOKEN-EFFICIENT: Concise syntax minimizes context usage")
    print("  3. HUMAN-READABLE: Musicians can read and verify LLM output")
    print("  4. PARSEABLE: Structured format enables programmatic analysis")

    print("\nPotential LLM Applications:")
    print("  • Chord reharmonization (as demonstrated)")
    print("  • Style transfer (e.g., pop → jazz)")
    print("  • Chord progression generation")
    print("  • Harmonic analysis and suggestions")
    print("  • Automatic accompaniment generation")

    print(f"\n{'=' * 70}\n")


def main():
    """
    Main entry point for the demo script.

    Runs the reharmonization demo and prints instructions for real LLM integration.
    """
    demo_reharmonization()

    print("\nTo integrate with a real LLM:")
    print("\n# Using Anthropic Claude:")
    print("pip install anthropic")
    print("export ANTHROPIC_API_KEY='your-key'")
    print("""
import anthropic

def reharmonize_with_claude(noten_input):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = create_reharmonization_prompt(noten_input)

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
""")

    print("\n# Using OpenAI GPT:")
    print("pip install openai")
    print("export OPENAI_API_KEY='your-key'")
    print("""
import openai

def reharmonize_with_gpt(noten_input):
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = create_reharmonization_prompt(noten_input)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
""")


if __name__ == '__main__':
    main()
