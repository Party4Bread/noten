import sys
import os

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from noten.noten_parser import parse
from noten.noten_rhythm import calculate_durations, print_rhythm_analysis

def main():
    print("Noten Rhythm Analysis Demo")
    print("==========================")

    # Example song with various rhythm features
    # 1. Basic chords
    # 2. Tuplets (triplets)
    # 3. Continuation markers crossing bar lines (The fix!)

    noten_input = """{title: Rhythm Demo}
{key: C}
{time: 4/4}

{Section A}
| Cmaj7 . . G | (Am G F) C |
|: C | % :| x2

{Bridge}
| F . . . | . . G . |
"""

    print(f"\nInput Noten:\n{noten_input}")

    # 1. Parse the input
    print("Parsing...")
    ast = parse(noten_input)

    # 2. Calculate durations
    print("Calculating durations...")
    events = calculate_durations(ast.to_dict())

    # 3. Print analysis
    print("\nRhythm Analysis:")
    print_rhythm_analysis(events)

    print("\nNote how the F in the Bridge lasts for 4+2=6 beats due to the continuation markers in the next measure.")

if __name__ == "__main__":
    main()
