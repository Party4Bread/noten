"""
Noten Parser - Builds an Abstract Syntax Tree from tokens.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .noten_lexer import Token, TokenType, tokenize


# AST Node Classes

@dataclass
class ChordNode:
    """
    Represents a single chord.

    Attributes:
        type: Node type identifier (always "Chord").
        root: The root note of the chord (e.g., "C", "F#").
        quality: The chord quality and extensions (e.g., "maj7", "m").
        bass: Optional bass note for slash chords (e.g., "B" in "G/B").
    """
    type: str = "Chord"
    root: str = ""
    quality: str = ""
    bass: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the chord node to a dictionary representation.

        Returns:
            A dictionary containing the chord's type, root, quality, and bass.
        """
        return {
            "type": self.type,
            "root": self.root,
            "quality": self.quality,
            "bass": self.bass
        }


@dataclass
class ContinuationNode:
    """
    Represents a continuation marker (.).

    This node indicates that the previous chord's duration should be extended.

    Attributes:
        type: Node type identifier (always "Continuation").
    """
    type: str = "Continuation"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the continuation node to a dictionary representation.

        Returns:
            A dictionary containing the node type.
        """
        return {"type": self.type}


@dataclass
class TupletNode:
    """
    Represents a tuplet group of chords.

    A tuplet groups multiple chords that share a single beat's duration.

    Attributes:
        type: Node type identifier (always "Tuplet").
        chords: List of ChordNodes within this tuplet.
    """
    type: str = "Tuplet"
    chords: List[ChordNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tuplet node to a dictionary representation.

        Returns:
            A dictionary containing the node type and list of chord dictionaries.
        """
        return {
            "type": self.type,
            "chords": [c.to_dict() for c in self.chords]
        }


@dataclass
class MeasureNode:
    """
    Represents a standard measure with beat markers.

    Attributes:
        type: Node type identifier (always "Measure").
        beats: List of beat elements (ChordNode, TupletNode, or ContinuationNode).
    """
    type: str = "Measure"
    beats: List[Any] = field(default_factory=list)  # ChordNode, TupletNode, or ContinuationNode

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the measure node to a dictionary representation.

        Returns:
            A dictionary containing the node type and list of beat dictionaries.
        """
        return {
            "type": self.type,
            "beats": [b.to_dict() for b in self.beats]
        }


@dataclass
class RepeatMeasureNode:
    """
    Represents a measure repeat (% or %xN).

    Indicates that the previous measure content should be repeated.

    Attributes:
        type: Node type identifier (always "RepeatMeasure").
        count: Number of times to repeat (default is 1).
    """
    type: str = "RepeatMeasure"
    count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the repeat measure node to a dictionary representation.

        Returns:
            A dictionary containing the node type and repeat count.
        """
        return {
            "type": self.type,
            "count": self.count
        }


@dataclass
class RepeatSectionNode:
    """
    Represents a repeat section (|: ... :|).

    Contains a sequence of measures that are repeated a specified number of times.

    Attributes:
        type: Node type identifier (always "RepeatSection").
        measures: List of measures within the repeat section.
        repeat_count: Total number of times this section is played (default is 1).
    """
    type: str = "RepeatSection"
    measures: List[Any] = field(default_factory=list)  # MeasureNode or RepeatMeasureNode
    repeat_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the repeat section node to a dictionary representation.

        Returns:
            A dictionary containing the node type, repeat count, and list of measure dictionaries.
        """
        return {
            "type": self.type,
            "repeatCount": self.repeat_count,
            "measures": [m.to_dict() for m in self.measures]
        }


@dataclass
class MeasureLineNode:
    """
    Represents a line of measures.

    This corresponds to a single line of input text containing one or more measures.

    Attributes:
        type: Node type identifier (always "MeasureLine").
        measures: List of measures (MeasureNode, RepeatMeasureNode, or RepeatSectionNode).
    """
    type: str = "MeasureLine"
    measures: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the measure line node to a dictionary representation.

        Returns:
            A dictionary containing the node type and list of measure dictionaries.
        """
        return {
            "type": self.type,
            "measures": [m.to_dict() for m in self.measures]
        }


@dataclass
class AnnotationNode:
    """
    Represents an annotation block.

    Annotations are metadata or directives enclosed in curly braces, e.g., {title: ...}.

    Attributes:
        type: Node type identifier (always "Annotation").
        content: The text content inside the annotation braces.
    """
    type: str = "Annotation"
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the annotation node to a dictionary representation.

        Returns:
            A dictionary containing the node type and annotation content.
        """
        return {
            "type": self.type,
            "content": self.content
        }


@dataclass
class SongNode:
    """
    Root AST node representing the entire song.

    Attributes:
        type: Node type identifier (always "Song").
        body: List of top-level nodes (AnnotationNode or MeasureLineNode).
    """
    type: str = "Song"
    body: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the song node to a dictionary representation.

        Returns:
            A dictionary containing the node type and list of body element dictionaries.
        """
        return {
            "type": self.type,
            "body": [node.to_dict() for node in self.body]
        }


class ChordParser:
    """
    Parses chord symbols into root, quality, and bass components.

    This utility class handles the complexities of chord syntax, including
    slashes for bass notes and special cases like "N.C.".
    """

    @staticmethod
    def parse(chord_str: str) -> ChordNode:
        """
        Parse a chord string into components.

        Examples:
            "C" -> root="C", quality="", bass=None
            "Cmaj7" -> root="C", quality="maj7", bass=None
            "Am" -> root="A", quality="m", bass=None
            "G/B" -> root="G", quality="", bass="B"
            "Am7/G" -> root="A", quality="m7", bass="G"
            "N.C." -> root="N.C.", quality="", bass=None

        Args:
            chord_str: The chord symbol string to parse.

        Returns:
            ChordNode: A ChordNode object containing the parsed root, quality, and bass.

        Raises:
            ValueError: If the chord string is invalid or cannot be parsed.
        """
        # Special case: No Chord
        if chord_str == "N.C.":
            return ChordNode(root="N.C.", quality="", bass=None)

        # Check for slash chord (bass note)
        bass = None
        if '/' in chord_str:
            chord_str, bass = chord_str.split('/', 1)

        # Extract root note (A-G with optional # or b)
        root_pattern = r'^([A-G][#b]?)'
        match = re.match(root_pattern, chord_str)

        if not match:
            raise ValueError(f"Invalid chord: {chord_str}")

        root = match.group(1)
        quality = chord_str[len(root):]  # Everything after the root

        return ChordNode(root=root, quality=quality, bass=bass)


class NotenParser:
    """
    Parser for the Noten (LLM-Chart) format.

    Consumes tokens and builds an Abstract Syntax Tree according to
    the grammar in Section 3.1 of the specification.

    Attributes:
        tokens: The list of tokens to parse.
        position: The current index in the token list.
    """

    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a token stream.

        Args:
            tokens: List of tokens from the lexer.
        """
        self.tokens = tokens
        self.position = 0

    def parse(self) -> SongNode:
        """
        Parse the token stream into an AST.

        Iterates through the tokens and constructs the song structure,
        including annotations and measure lines.

        Returns:
            SongNode: The root node representing the entire song.

        Raises:
            ValueError: If an unexpected token is encountered.
        """
        song = SongNode()

        while not self._is_at_end():
            # Skip extra newlines
            if self._check(TokenType.NEWLINE):
                self._advance()
                continue

            # Parse annotation or measure line
            if self._check(TokenType.ANNOTATION_START):
                song.body.append(self._parse_annotation())
            elif self._is_measure_start():
                song.body.append(self._parse_measure_line())
            else:
                # Unexpected token
                current = self._peek()
                raise ValueError(
                    f"Unexpected token {current.type.name} at line {current.line}"
                )

        return song

    def _parse_annotation(self) -> AnnotationNode:
        """Parse an annotation line: { content }"""
        self._consume(TokenType.ANNOTATION_START, "Expected '{'")
        content = self._consume(TokenType.ANNOTATION_CONTENT, "Expected annotation content").value
        self._consume(TokenType.ANNOTATION_END, "Expected '}'")

        # Consume optional newline
        if self._check(TokenType.NEWLINE):
            self._advance()

        return AnnotationNode(content=content)

    def _parse_measure_line(self) -> MeasureLineNode:
        """Parse a line of measures."""
        measure_line = MeasureLineNode()

        # Parse measures until we hit a newline or EOF
        while not self._is_at_end() and not self._check(TokenType.NEWLINE):
            if self._check(TokenType.REPEAT_START):
                measure_line.measures.append(self._parse_repeat_section())
            elif self._check(TokenType.SINGLE_REPEAT):
                measure_line.measures.append(self._parse_repeat_measure())
            elif self._check(TokenType.MULTI_REPEAT):
                # Handle trailing x2 after a measure
                if not measure_line.measures:
                    raise ValueError("Unexpected repeat count at start of line")
                count = self._parse_multi_repeat_count()
                # Attach to last measure
                last = measure_line.measures[-1]
                # If it's a regular measure, we attach the count.
                # If it's a repeat section, it should have been handled inside _parse_repeat_section,
                # but if it's external (e.g. |: ... :| x2), it's also handled there.
                # If it's a repeat measure (%), it's handled in _parse_repeat_measure.
                # So this is mainly for | C | x2 case where x2 is after the closing bar.
                if isinstance(last, MeasureNode):
                    last.repeat_count = count  # type: ignore
                elif isinstance(last, RepeatMeasureNode):
                     # Should have been handled in _parse_repeat_measure but if written as | % | x2
                     last.count = count * last.count
                else:
                     # RepeatSectionNode handled internally, but if we see another x2?
                     # Treat as multiply?
                     last.repeat_count = last.repeat_count * count

            elif self._check(TokenType.BAR_START):
                # Check if this BAR_START is followed by SINGLE_REPEAT (e.g., | % |)
                if self.position + 1 < len(self.tokens) and self.tokens[self.position + 1].type == TokenType.SINGLE_REPEAT:
                    self._advance()  # consume opening |
                    measure_line.measures.append(self._parse_repeat_measure())

                    # Check for closing |
                    if self._check(TokenType.BAR_START):
                        # Logic to decide whether to consume closing |
                        # Similar to _parse_measure logic but applied here
                        if self.position + 1 < len(self.tokens):
                            next_token = self.tokens[self.position + 1]
                            if next_token.type in (TokenType.NEWLINE, TokenType.MULTI_REPEAT):
                                self._advance()
                        elif self.position + 1 >= len(self.tokens):
                            self._advance()
                    else:
                        # Allow missing closing | if followed by newline/EOF?
                        # _parse_measure enforces closing bar if not at EOF/newline.
                        pass
                else:
                    measure_line.measures.append(self._parse_measure())
                    # After parsing a measure, we're positioned at the closing |
                    # If the next token (after |) is a newline/EOF or MULTI_REPEAT, consume the |
                    # Otherwise, leave it for the next measure
                    if self._check(TokenType.BAR_START):
                        # Peek ahead to see what's after this |
                        if self.position + 1 < len(self.tokens):
                            next_token = self.tokens[self.position + 1]
                            if next_token.type in (TokenType.NEWLINE, TokenType.MULTI_REPEAT):
                                # This | is a closing bar, consume it
                                self._advance()
                        elif self.position + 1 >= len(self.tokens):
                            # EOF after |, consume it
                            self._advance()
            else:
                break

        # Consume newline at end of measure line
        if self._check(TokenType.NEWLINE):
            self._advance()

        return measure_line

    def _parse_measure(self) -> MeasureNode:
        """Parse a single measure: | content |"""
        self._consume(TokenType.BAR_START, "Expected '|'")

        measure = MeasureNode()
        measure.beats = self._parse_measure_content()

        # Don't consume the closing | - let the measure line handler deal with it
        # Just verify we're at a bar boundary
        if not self._is_bar_end():
            raise ValueError(f"Expected closing '|', got {self._peek().type.name if not self._is_at_end() else 'EOF'}")

        # Check for multi-repeat after measure (only if there's no closing bar yet)
        if self._check(TokenType.MULTI_REPEAT):
            count = self._parse_multi_repeat_count()
            # Wrap in repeat structure - for now, just note it
            # (full expansion would happen in a separate step)
            measure.repeat_count = count  # type: ignore

        return measure

    def _parse_repeat_measure(self) -> RepeatMeasureNode:
        """Parse a repeat measure: % or %xN"""
        self._consume(TokenType.SINGLE_REPEAT, "Expected '%'")

        count = 1
        if self._check(TokenType.MULTI_REPEAT):
            count = self._parse_multi_repeat_count()

        return RepeatMeasureNode(count=count)

    def _parse_repeat_section(self) -> RepeatSectionNode:
        """Parse a repeat section: |: ... :|"""
        self._consume(TokenType.REPEAT_START, "Expected '|:'")

        section = RepeatSectionNode()

        # Parse first element (could be a measure content, or a repeat measure %)
        if self._check(TokenType.SINGLE_REPEAT):
            section.measures.append(self._parse_repeat_measure())
        else:
            # Try to parse measure content
            beats = self._parse_measure_content()
            # If we got beats, it's a measure.
            # If beats is empty, check if we hit a bar start (empty measure) or repeat end
            if beats or self._check(TokenType.BAR_START) or self._check(TokenType.REPEAT_END):
                 measure = MeasureNode(beats=beats)
                 section.measures.append(measure)
            # If we still have SINGLE_REPEAT here, it means _parse_measure_content stopped at it
            # This handles |: C % :| where C is parsed, loop breaks at %, but we need to verify
            # if we are at the start of a "measure" context.

            # Wait, _parse_measure_content eats until bar end or %.
            # If it eats 'C' and sees '%', it returns [C]. Next token is %.
            # But here we are at the "first measure".
            # If the input is |: % :|, we enter else block. _parse_measure_content sees %, returns empty list.
            # Next token is %.
            # So if beats is empty and next token is %, we should handle it as repeat measure?
            elif self._check(TokenType.SINGLE_REPEAT):
                 section.measures.append(self._parse_repeat_measure())


        # Parse additional measures within the repeat section
        while self._check(TokenType.BAR_START) or self._check(TokenType.SINGLE_REPEAT):
            if self._check(TokenType.SINGLE_REPEAT):
                 # This handles case where we have implicit measure boundaries or just %
                 section.measures.append(self._parse_repeat_measure())
                 continue

            # It's a BAR_START
            self._advance()  # consume BAR_START

            if self._check(TokenType.SINGLE_REPEAT):
                section.measures.append(self._parse_repeat_measure())
            elif self._check(TokenType.REPEAT_END):
                 # Empty measure at end? |: C | :|
                 break
            else:
                measure = MeasureNode(beats=self._parse_measure_content())
                section.measures.append(measure)

        self._consume(TokenType.REPEAT_END, "Expected ':|'")

        # Check for multi-repeat
        if self._check(TokenType.MULTI_REPEAT):
            section.repeat_count = self._parse_multi_repeat_count()

        return section

    def _parse_measure_content(self) -> List[Any]:
        """Parse the content within a measure."""
        beats = []

        while not self._is_bar_end() and not self._is_at_end():
            if self._check(TokenType.CHORD) or self._check(TokenType.NO_CHORD):
                chord_token = self._advance()
                beats.append(ChordParser.parse(chord_token.value))
            elif self._check(TokenType.CONTINUATION):
                self._advance()
                beats.append(ContinuationNode())
            elif self._check(TokenType.TUPLET_START):
                beats.append(self._parse_tuplet())
            elif self._check(TokenType.SINGLE_REPEAT):
                # % inside a measure content (within repeat section)
                break
            else:
                break

        return beats

    def _parse_tuplet(self) -> TupletNode:
        """Parse a tuplet: (chords)"""
        self._consume(TokenType.TUPLET_START, "Expected '('")

        tuplet = TupletNode()

        while not self._check(TokenType.TUPLET_END) and not self._is_at_end():
            if self._check(TokenType.CHORD) or self._check(TokenType.NO_CHORD):
                chord_token = self._advance()
                tuplet.chords.append(ChordParser.parse(chord_token.value))
            else:
                break

        self._consume(TokenType.TUPLET_END, "Expected ')'")

        return tuplet

    def _parse_multi_repeat_count(self) -> int:
        """Parse a multi-repeat count (xN or %xN) and return the number."""
        token = self._consume(TokenType.MULTI_REPEAT, "Expected repeat count")
        # Extract number from "x3" or "%x3"
        match = re.search(r'x(\d+)', token.value)
        if match:
            return int(match.group(1))
        return 1

    def _is_measure_start(self) -> bool:
        """Check if current token starts a measure."""
        return (self._check(TokenType.BAR_START) or
                self._check(TokenType.REPEAT_START) or
                self._check(TokenType.SINGLE_REPEAT))

    def _is_bar_end(self) -> bool:
        """Check if current token ends a bar."""
        return (self._check(TokenType.BAR_START) or  # | serves as both start and end
                self._check(TokenType.REPEAT_END) or
                self._check(TokenType.NEWLINE))

    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type."""
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _peek(self) -> Token:
        """Return current token without advancing."""
        return self.tokens[self.position]

    def _advance(self) -> Token:
        """Consume and return current token."""
        token = self._peek()
        if not self._is_at_end():
            self.position += 1
        return token

    def _consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of expected type or raise error."""
        if self._check(token_type):
            return self._advance()

        current = self._peek() if not self._is_at_end() else None
        error_msg = f"{message}. Got {current.type.name if current else 'EOF'}"
        if current:
            error_msg += f" at line {current.line}"
        raise ValueError(error_msg)

    def _is_at_end(self) -> bool:
        """Check if we've consumed all tokens."""
        return self.position >= len(self.tokens)


def parse(input_text: str) -> SongNode:
    """
    Convenience function to parse noten input directly from text.

    This is the main entry point for parsing Noten format strings. It handles
    tokenization and parsing in a single step.

    Args:
        input_text: The noten format string to be parsed.

    Returns:
        SongNode: The root node of the resulting Abstract Syntax Tree (AST).

    Raises:
        ValueError: If parsing fails due to invalid syntax or unexpected tokens.
    """
    tokens = tokenize(input_text, include_whitespace=False)
    parser = NotenParser(tokens)
    return parser.parse()


if __name__ == '__main__':
    import json

    # Test the parser with the example from the spec
    test_input = """{title: LLM-Chart Demo}
{key: C}
{time: 4/4}

{Verse 1}
| Cmaj7 . . G | (Am G F) C |
|: C | % :| x2
"""

    print("Testing Noten Parser")
    print("=" * 60)
    print("Input:")
    print(test_input)
    print("\n" + "=" * 60)
    print("AST (JSON):\n")

    ast = parse(test_input)
    print(json.dumps(ast.to_dict(), indent=2))
