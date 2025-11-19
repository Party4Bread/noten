"""
Noten Real LLM Demo: Chord Reharmonization with Actual LLM Integration

This demo uses litellm to test the noten format with real LLM APIs.
"""

import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import litellm
from noten import parse, calculate_durations, print_rhythm_analysis


# Load environment variables
load_dotenv()


def create_reharmonization_prompt(noten_input: str, style: str = "jazz") -> str:
    """
    Create a prompt for LLM chord reharmonization.

    Args:
        noten_input: Original chord progression in noten format
        style: Target style (jazz, bossa nova, gospel, etc.)

    Returns:
        Formatted prompt for the LLM
    """
    prompt = f"""You are an expert music arranger. I'll provide a chord progression in "noten" format, and you should reharmonize it in {style} style.

NOTEN FORMAT SPECIFICATION:
- Annotations in curly braces: {{key: C}}, {{time: 4/4}}, {{title: Song Name}}
- Measures between bar lines: | C . . G | (chords and continuations)
- Continuation marker ".": extends the previous chord's duration
- Tuplets in parentheses: (Am G F) groups chords within a beat
- Repeat sections: |: C | D :| x2 means play that section 2 times total
- Single measure repeat: % repeats the previous measure

CHORD FORMAT EXAMPLES:
- C, G, Am (root + quality)
- Cmaj7, G13, Am9 (with extensions)
- G7b9, Am7#11 (with alterations)
- G/B, Am7/G (slash chords for bass notes)

CRITICAL RULES FOR YOUR OUTPUT:
1. Output ONLY valid noten format - no explanations, no markdown code blocks, no extra text
2. Start immediately with annotations: {{title: ...}}, {{key: ...}}, {{time: ...}}
3. Maintain the EXACT same rhythm structure (same number of beats per measure)
4. Use the continuation marker "." correctly to preserve timing
5. Keep the same number of measures as the original
6. Each measure must have the same total beats (count dots correctly!)
7. All chord symbols must be valid: root note (A-G) + optional accidentals (#/b) + optional quality + optional /bass

ORIGINAL PROGRESSION:
{noten_input}

Please reharmonize this progression in {style} style. Use sophisticated chord extensions and substitutions appropriate for {style}.

OUTPUT ONLY THE NOTEN FORMAT (start with {{title: }} immediately, no other text):"""

    return prompt


def call_llm(prompt: str, model: str = "claude-3-5-sonnet-20241022") -> str:
    """
    Call LLM using litellm.

    Args:
        prompt: The prompt to send
        model: Model identifier (e.g., "anthropic/claude-3-5-sonnet-20241022")

    Returns:
        LLM response text
    """
    print(f"\n🤖 Calling LLM: {model}")
    print(f"   (This may take 10-30 seconds...)")

    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"\n❌ Error calling LLM: {e}")
        raise


def extract_noten_from_response(response: str) -> str:
    """
    Extract noten format from LLM response (in case there's extra text).

    Args:
        response: LLM response text

    Returns:
        Extracted noten format string
    """
    # Remove markdown code blocks if present
    response = response.strip()
    if response.startswith('```'):
        lines = response.split('\n')
        # Remove first line (```noten or ```) and last line (```)
        if lines[-1].strip() == '```':
            lines = lines[1:-1]
        response = '\n'.join(lines)

    # If response starts with {, assume it's pure noten
    if response.strip().startswith('{'):
        return response.strip()

    # Try to find noten block between markers
    lines = response.split('\n')
    noten_lines = []
    in_noten = False

    for line in lines:
        # Start collecting when we see an annotation
        if line.strip().startswith('{'):
            in_noten = True

        if in_noten:
            noten_lines.append(line)

    result = '\n'.join(noten_lines)

    # Validate basic noten structure
    if not result.strip():
        raise ValueError("No noten format found in LLM response")

    if not result.strip().startswith('{'):
        raise ValueError("Response doesn't start with annotation")

    return result


def analyze_progression(noten_input: str, title: str = "Progression") -> tuple[Optional[Dict[str, Any]], Optional[list]]:
    """
    Parse and analyze a noten progression.

    Args:
        noten_input: Chord progression in noten format
        title: Title for display

    Returns:
        Tuple of (ast_dict, events) or (None, None) if parsing fails
    """
    print(f"\n{'═' * 70}")
    print(f"{title}")
    print(f"{'═' * 70}")
    print("\n📝 Noten Format:")
    print(noten_input)

    try:
        ast = parse(noten_input)
        ast_dict = ast.to_dict()

        print("\n" + "─" * 70)
        print("✓ Successfully Parsed!")
        print("─" * 70)

        # Extract metadata
        annotations = [n for n in ast_dict['body'] if n['type'] == 'Annotation']
        if annotations:
            print("\n📋 Metadata:")
            for anno in annotations:
                print(f"   • {anno['content']}")

        # Calculate rhythm
        events = calculate_durations(ast_dict)

        print(f"\n🎵 Rhythm Analysis:")
        print("─" * 70)
        print_rhythm_analysis(events)

        # Statistics
        if events:
            total_duration = max(e['start'] + e['duration'] for e in events)
            total_measures = float(total_duration) / 4  # Assuming 4/4
            print(f"\n📊 Statistics:")
            print(f"   • Total chords: {len(events)}")
            print(f"   • Duration: {float(total_duration)} beats ({total_measures} measures)")

        return ast_dict, events

    except Exception as e:
        print(f"\n❌ Error parsing noten: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def compare_progressions(original_events, reharmonized_events):
    """
    Compare original and reharmonized progressions.

    Args:
        original_events: Rhythm events from original
        reharmonized_events: Rhythm events from reharmonization
    """
    print(f"\n{'═' * 70}")
    print("COMPARISON: Original vs Reharmonized")
    print(f"{'═' * 70}")

    print(f"\n📊 Chord Count:")
    print(f"   • Original: {len(original_events)} chords")
    print(f"   • Reharmonized: {len(reharmonized_events)} chords")

    print("\n🎼 Side-by-side (first 15 events):")
    print(f"{'Time':<8} {'Original':<25} {'Reharmonized':<25}")
    print("─" * 70)

    max_events = max(len(original_events), len(reharmonized_events))
    for i in range(min(15, max_events)):
        time_str = f"{float(original_events[i]['start']):.1f}" if i < len(original_events) else "-"

        if i < len(original_events):
            orig_chord = original_events[i]['chord']
            orig_str = f"{orig_chord['root']}{orig_chord['quality']}"
            if orig_chord.get('bass'):
                orig_str += f"/{orig_chord['bass']}"
        else:
            orig_str = "-"

        if i < len(reharmonized_events):
            reh_chord = reharmonized_events[i]['chord']
            reh_str = f"{reh_chord['root']}{reh_chord['quality']}"
            if reh_chord.get('bass'):
                reh_str += f"/{reh_chord['bass']}"
        else:
            reh_str = "-"

        print(f"{time_str:<8} {orig_str:<25} {reh_str:<25}")

    if max_events > 15:
        print(f"   ... ({max_events - 15} more events)")


def demo_interactive():
    """
    Interactive demo allowing user to choose options.
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         NOTEN REAL LLM DEMO: Chord Reharmonization              ║
║                                                                  ║
║  Testing the noten format with real LLM APIs using litellm      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

    # Check API keys
    print("🔑 Checking available API keys...")
    available_models = []

    if os.getenv('ANTHROPIC_API_KEY'):
        available_models.append(("Claude 3.5 Sonnet", "claude-3-5-sonnet-latest"))
        print("   ✓ Anthropic API key found")

    if os.getenv('OPENAI_API_KEY'):
        available_models.append(("GPT-4o", "gpt-4o"))
        print("   ✓ OpenAI API key found")

    if os.getenv('GEMINI_API_KEY'):
        available_models.append(("Gemini Pro", "gemini/gemini-2.0-flash-exp"))
        print("   ✓ Gemini API key found")

    if os.getenv('OPENROUTER_API_KEY'):
        available_models.append(("OpenRouter (Claude)", "openrouter/anthropic/claude-3.5-sonnet"))
        print("   ✓ OpenRouter API key found")

    if not available_models:
        print("\n❌ No API keys found in .env file!")
        print("   Please add at least one API key to continue.")
        return

    # Select model
    print(f"\n📋 Available models:")
    for i, (name, _) in enumerate(available_models, 1):
        print(f"   {i}. {name}")

    choice = input(f"\nSelect model (1-{len(available_models)}, default=1): ").strip()
    if not choice:
        choice = "1"

    try:
        model_idx = int(choice) - 1
        model_name, model_id = available_models[model_idx]
    except:
        print("Invalid choice, using first model")
        model_name, model_id = available_models[0]

    print(f"\n✓ Selected: {model_name}")

    # Select example or custom input
    print("\n📝 Choose input:")
    print("   1. Simple pop progression (C G Am F)")
    print("   2. Jazz ii-V-I progression")
    print("   3. Blues progression")
    print("   4. Custom input")

    example_choice = input("\nSelect (1-4, default=1): ").strip()
    if not example_choice:
        example_choice = "1"

    if example_choice == "1":
        original_progression = """{title: Simple Pop Song}
{key: C}
{time: 4/4}

{Verse}
| C . . . | G . . . |
| Am . . . | F . . . |
| C . . . | G . . . |
| F . . . | G . . . |
"""
        style = "jazz"

    elif example_choice == "2":
        original_progression = """{title: ii-V-I in C}
{key: C}
{time: 4/4}

{Progression}
| Dm7 . . . | G7 . . . |
| Cmaj7 . . . | Cmaj7 . . . |
"""
        style = "bebop jazz"

    elif example_choice == "3":
        original_progression = """{title: 12-Bar Blues}
{key: C}
{time: 4/4}

{Blues}
| C7 . . . | C7 . . . | C7 . . . | C7 . . . |
| F7 . . . | F7 . . . | C7 . . . | C7 . . . |
| G7 . . . | F7 . . . | C7 . . . | G7 . . . |
"""
        style = "jazz blues"

    else:
        print("\nEnter your noten progression (end with empty line):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        original_progression = '\n'.join(lines)
        style = input("Reharmonization style (default=jazz): ").strip() or "jazz"

    # Run the demo
    print("\n" + "═" * 70)
    print("STEP 1: Analyzing Original Progression")
    original_ast, original_events = analyze_progression(
        original_progression,
        title="ORIGINAL PROGRESSION"
    )

    if not original_ast:
        print("\n❌ Failed to parse original progression. Exiting.")
        return

    # Generate prompt
    print("\n" + "═" * 70)
    print("STEP 2: Generating LLM Prompt")
    print("═" * 70)
    prompt = create_reharmonization_prompt(original_progression, style)
    print(f"\n📝 Prompt length: {len(prompt)} characters")
    print(f"🎯 Target style: {style}")

    # Call LLM
    print("\n" + "═" * 70)
    print("STEP 3: Calling LLM for Reharmonization")
    print("═" * 70)

    try:
        llm_response = call_llm(prompt, model_id)
        print(f"\n✓ Received response ({len(llm_response)} characters)")

        # Extract noten format
        reharmonized = extract_noten_from_response(llm_response)

        # Analyze reharmonization
        print("\n" + "═" * 70)
        print("STEP 4: Analyzing Reharmonized Progression")
        reharmonized_ast, reharmonized_events = analyze_progression(
            reharmonized,
            title="REHARMONIZED PROGRESSION"
        )

        if not reharmonized_ast:
            print("\n⚠️  LLM output was not valid noten format")
            print("\n📄 Raw LLM Response:")
            print(llm_response)
            return

        # Compare
        compare_progressions(original_events, reharmonized_events)

        # Success summary
        print(f"\n{'═' * 70}")
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print(f"{'═' * 70}")
        print("\n🎉 Key Achievements:")
        print("   ✓ Original noten parsed correctly")
        print(f"   ✓ LLM ({model_name}) understood noten format")
        print("   ✓ LLM generated valid noten output")
        print("   ✓ Reharmonized output parsed successfully")
        print("   ✓ Format is LLM-compatible and bidirectional!")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    demo_interactive()
