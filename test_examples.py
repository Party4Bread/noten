"""
Test all example noten files to ensure they parse correctly.
"""

import os
from noten import parse, calculate_durations, print_rhythm_analysis


def test_example_file(filepath):
    """
    Test parsing and rhythm analysis for an example file.

    Args:
        filepath: Path to the .noten file

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'=' * 70}")
    print(f"Testing: {os.path.basename(filepath)}")
    print(f"{'=' * 70}")

    try:
        # Read file
        with open(filepath, 'r') as f:
            content = f.read()

        print("\nContent preview (first 300 chars):")
        print(content[:300] + ("..." if len(content) > 300 else ""))

        # Parse
        ast = parse(content)
        ast_dict = ast.to_dict()

        # Extract metadata
        annotations = [n for n in ast_dict['body'] if n['type'] == 'Annotation']
        print(f"\n✓ Parsed successfully")
        print(f"  Annotations: {len(annotations)}")

        for anno in annotations[:5]:  # Show first 5
            print(f"    - {anno['content']}")

        # Count measures
        measure_lines = [n for n in ast_dict['body'] if n['type'] == 'MeasureLine']
        total_measures = sum(len(ml['measures']) for ml in measure_lines)
        print(f"  Measure lines: {len(measure_lines)}")
        print(f"  Total measures: {total_measures}")

        # Calculate rhythm
        events = calculate_durations(ast_dict)
        print(f"  Chord events: {len(events)}")

        if events:
            total_duration = max(e['start'] + e['duration'] for e in events)
            total_bars = float(total_duration) / 4  # Assuming 4/4
            print(f"  Total duration: {float(total_duration):.1f} beats ({total_bars:.1f} measures)")

            # Show first few chords
            print(f"\n  First few chords:")
            for i, event in enumerate(events[:8]):
                chord = event['chord']
                chord_str = f"{chord['root']}{chord['quality']}"
                if chord.get('bass'):
                    chord_str += f"/{chord['bass']}"
                tuplet = " (tuplet)" if event.get('in_tuplet') else ""
                print(f"    {i+1}. Beat {float(event['start']):.1f}: {chord_str} for {float(event['duration']):.2f} beats{tuplet}")

        print(f"\n✓ {os.path.basename(filepath)} - ALL CHECKS PASSED")
        return True

    except Exception as e:
        print(f"\n✗ {os.path.basename(filepath)} - FAILED")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_examples():
    """Test all example files."""
    print("=" * 70)
    print("TESTING ALL EXAMPLE NOTEN FILES")
    print("=" * 70)

    examples_dir = os.path.join(os.path.dirname(__file__), 'examples')

    if not os.path.exists(examples_dir):
        print(f"\n✗ Examples directory not found: {examples_dir}")
        return False

    # Find all .noten files
    noten_files = [f for f in os.listdir(examples_dir) if f.endswith('.noten')]

    if not noten_files:
        print(f"\n✗ No .noten files found in {examples_dir}")
        return False

    print(f"\nFound {len(noten_files)} example files:")
    for f in noten_files:
        print(f"  - {f}")

    # Test each file
    results = {}
    for filename in sorted(noten_files):
        filepath = os.path.join(examples_dir, filename)
        results[filename] = test_example_file(filepath)

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for filename, success in sorted(results.items()):
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {filename}")

    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} files")

    return failed == 0


if __name__ == '__main__':
    success = test_all_examples()
    exit(0 if success else 1)
