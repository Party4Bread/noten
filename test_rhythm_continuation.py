
import unittest
from noten.noten_parser import parse
from noten.noten_rhythm import calculate_durations
from fractions import Fraction

class TestContinuationBug(unittest.TestCase):
    def test_continuation_across_measures(self):
        # Input: | C . . . | . . G . |
        # Measure 1: C (1 beat) + 3 continuations = 4 beats
        # Measure 2: 2 continuations + G (1 beat) + 1 continuation
        # The 2 continuations at start of Measure 2 should extend C.
        # So C should be 4 + 2 = 6 beats.
        # G should be 1 + 1 = 2 beats.

        input_text = """
| C . . . | . . G . |
"""
        ast = parse(input_text)
        events = calculate_durations(ast.to_dict())

        # Expected events:
        # 1. Chord C, start=0, duration=6
        # 2. Chord G, start=6, duration=2

        self.assertEqual(len(events), 2)

        c_event = events[0]
        self.assertEqual(c_event['chord']['root'], 'C')
        self.assertEqual(c_event['start'], 0)
        self.assertEqual(c_event['duration'], 6.0)

        g_event = events[1]
        self.assertEqual(g_event['chord']['root'], 'G')
        self.assertEqual(g_event['start'], 6.0)
        self.assertEqual(g_event['duration'], 2.0)

if __name__ == '__main__':
    unittest.main()
