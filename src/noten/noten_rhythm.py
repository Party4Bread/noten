"""
Noten Rhythm Calculator - Calculates duration for each chord based on time signature.
"""

from typing import Dict, Any, List, Tuple
from fractions import Fraction


class TimeSignature:
    """Represents a time signature like 4/4, 3/4, 6/8, etc."""

    def __init__(self, signature_str: str = "4/4"):
        """
        Initialize time signature from string like "4/4".

        Args:
            signature_str: Time signature string (e.g., "4/4", "3/4", "6/8")
        """
        parts = signature_str.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid time signature: {signature_str}")

        self.numerator = int(parts[0])
        self.denominator = int(parts[1])

    @property
    def beats_per_measure(self) -> Fraction:
        """
        Get the total number of beats in one measure.

        Returns:
            Fraction representing beats per measure
        """
        # The numerator tells us how many beats, denominator tells us the note value
        # For 4/4: 4 beats per measure
        # For 3/4: 3 beats per measure
        # For 6/8: 6 eighth notes = 6 beats (in simple interpretation)
        return Fraction(self.numerator, 1)

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"


class RhythmCalculator:
    """
    Calculates rhythm durations for chords in a noten AST.

    Based on Section 2.2 of the specification:
    1. Time is divided equally among top-level elements in a measure
    2. Continuation markers extend the previous chord's duration
    3. Tuplets are single top-level elements with internal subdivision
    """

    def __init__(self, time_signature: TimeSignature = None):
        """
        Initialize the rhythm calculator.

        Args:
            time_signature: The time signature to use (defaults to 4/4)
        """
        self.time_signature = time_signature or TimeSignature("4/4")

    def calculate_song_durations(self, song_ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate durations for all chords in a song AST.

        Returns a flat list of chord events with timing information.

        Args:
            song_ast: The song AST dictionary

        Returns:
            List of chord events with start time and duration
        """
        events = []
        current_time = Fraction(0)

        # Extract time signature from annotations if present
        for node in song_ast.get('body', []):
            if node.get('type') == 'Annotation':
                content = node.get('content', '')
                if content.startswith('time:'):
                    time_str = content.split(':', 1)[1].strip()
                    self.time_signature = TimeSignature(time_str)
                    break

        # Process measure lines
        for node in song_ast.get('body', []):
            if node.get('type') == 'MeasureLine':
                measure_events = self._process_measure_line(node, current_time)
                events.extend(measure_events)
                # Update current time based on measures processed
                if measure_events:
                    last_event = measure_events[-1]
                    current_time = last_event['start'] + last_event['duration']

        return events

    def _process_measure_line(self, measure_line: Dict[str, Any], start_time: Fraction) -> List[Dict[str, Any]]:
        """Process a measure line and return chord events."""
        events = []
        current_time = start_time

        for measure in measure_line.get('measures', []):
            measure_events = self._process_measure(measure, current_time)
            events.extend(measure_events)
            if measure_events:
                last_event = measure_events[-1]
                current_time = last_event['start'] + last_event['duration']
            else:
                # Empty measure - advance by one measure duration
                current_time += self.time_signature.beats_per_measure

        return events

    def _process_measure(self, measure: Dict[str, Any], start_time: Fraction) -> List[Dict[str, Any]]:
        """Process a single measure and return chord events."""
        measure_type = measure.get('type')

        if measure_type == 'Measure':
            return self._process_standard_measure(measure, start_time)
        elif measure_type == 'RepeatMeasure':
            # Repeat measure: would need context of previous measure
            # For now, just return empty (full implementation would track previous measures)
            return []
        elif measure_type == 'RepeatSection':
            return self._process_repeat_section(measure, start_time)
        else:
            return []

    def _process_standard_measure(self, measure: Dict[str, Any], start_time: Fraction) -> List[Dict[str, Any]]:
        """
        Process a standard measure with beat markers.

        Implements the beat division rules from Section 2.2.
        """
        beats = measure.get('beats', [])
        if not beats:
            # Empty measure
            return []

        # Count top-level elements (chords, tuplets, and continuations each count as 1)
        num_elements = len(beats)

        # Calculate duration per element
        measure_duration = self.time_signature.beats_per_measure
        element_duration = measure_duration / num_elements

        events = []
        current_time = start_time
        last_chord_event = None

        for beat in beats:
            beat_type = beat.get('type')

            if beat_type == 'Chord':
                # Create chord event
                event = {
                    'type': 'chord',
                    'start': current_time,
                    'duration': element_duration,
                    'chord': beat
                }
                events.append(event)
                last_chord_event = event
                current_time += element_duration

            elif beat_type == 'Continuation':
                # Add this element's duration to the last chord
                if last_chord_event:
                    last_chord_event['duration'] += element_duration
                current_time += element_duration

            elif beat_type == 'Tuplet':
                # Process tuplet as a single top-level element
                tuplet_events = self._process_tuplet(beat, current_time, element_duration)
                events.extend(tuplet_events)
                if tuplet_events:
                    last_chord_event = tuplet_events[-1]
                current_time += element_duration

        return events

    def _process_tuplet(self, tuplet: Dict[str, Any], start_time: Fraction, total_duration: Fraction) -> List[Dict[str, Any]]:
        """
        Process a tuplet group.

        The chords within the tuplet divide the tuplet's total duration equally.
        """
        chords = tuplet.get('chords', [])
        if not chords:
            return []

        num_chords = len(chords)
        chord_duration = total_duration / num_chords

        events = []
        current_time = start_time

        for chord in chords:
            event = {
                'type': 'chord',
                'start': current_time,
                'duration': chord_duration,
                'chord': chord,
                'in_tuplet': True
            }
            events.append(event)
            current_time += chord_duration

        return events

    def _process_repeat_section(self, repeat_section: Dict[str, Any], start_time: Fraction) -> List[Dict[str, Any]]:
        """Process a repeat section, expanding it according to repeat count."""
        measures = repeat_section.get('measures', [])
        repeat_count = repeat_section.get('repeatCount', 1)

        all_events = []
        current_time = start_time

        # Process the section repeat_count times
        for _ in range(repeat_count):
            for measure in measures:
                measure_events = self._process_measure(measure, current_time)
                all_events.extend(measure_events)
                if measure_events:
                    last_event = measure_events[-1]
                    current_time = last_event['start'] + last_event['duration']
                else:
                    current_time += self.time_signature.beats_per_measure

        return all_events


def calculate_durations(song_ast: Dict[str, Any], time_signature: str = "4/4") -> List[Dict[str, Any]]:
    """
    Convenience function to calculate durations for a song AST.

    Args:
        song_ast: The song AST dictionary
        time_signature: Time signature string (default "4/4")

    Returns:
        List of chord events with timing information
    """
    calculator = RhythmCalculator(TimeSignature(time_signature))
    return calculator.calculate_song_durations(song_ast)


def print_rhythm_analysis(events: List[Dict[str, Any]]):
    """
    Pretty-print rhythm analysis.

    Args:
        events: List of chord events
    """
    print(f"{'Time':<10} {'Duration':<12} {'Chord':<15} {'Tuplet'}")
    print("-" * 60)

    for event in events:
        chord = event['chord']
        root = chord.get('root', '?')
        quality = chord.get('quality', '')
        bass = chord.get('bass')

        chord_str = f"{root}{quality}"
        if bass:
            chord_str += f"/{bass}"

        # Handle N.C. specially
        if root == "N.C.":
            chord_str = "N.C."

        start = event['start']
        duration = event['duration']
        in_tuplet = event.get('in_tuplet', False)

        # Format as decimal for readability
        start_str = f"{float(start):.2f}"
        duration_str = f"{float(duration):.3f}"

        tuplet_marker = "Yes" if in_tuplet else ""

        print(f"{start_str:<10} {duration_str:<12} {chord_str:<15} {tuplet_marker}")


if __name__ == '__main__':
    from noten_parser import parse
    import json

    # Test the rhythm calculator with the example from the spec
    test_input = """{title: LLM-Chart Demo}
{key: C}
{time: 4/4}

{Verse 1}
| Cmaj7 . . G | (Am G F) C |
|: C | % :| x2
"""

    print("Testing Noten Rhythm Calculator")
    print("=" * 60)
    print("Input:")
    print(test_input)
    print("\n" + "=" * 60)

    ast = parse(test_input)
    events = calculate_durations(ast.to_dict())

    print("\nRhythm Analysis:\n")
    print_rhythm_analysis(events)

    print("\n" + "=" * 60)
    print("\nDetailed Events (JSON):\n")
    # Convert Fraction to float for JSON serialization
    events_json = []
    for event in events:
        event_copy = event.copy()
        event_copy['start'] = float(event_copy['start'])
        event_copy['duration'] = float(event_copy['duration'])
        events_json.append(event_copy)

    print(json.dumps(events_json, indent=2))
