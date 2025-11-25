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
    """Represents a single chord."""
    type: str = "Chord"
    root: str = ""
    quality: str = ""
    bass: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "root": self.root,
            "quality": self.quality,
            "bass": self.bass
        }


@dataclass
class ContinuationNode:
    """Represents a continuation marker (.)."""
    type: str = "Continuation"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type}


@dataclass
class TupletNode:
    """Represents a tuplet group of chords."""
    type: str = "Tuplet"
    chords: List[ChordNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "chords": [c.to_dict() for c in self.chords]
        }


@dataclass
class MeasureNode:
    """Represents a standard measure with beat markers."""
    type: str = "Measure"
    beats: List[Any] = field(default_factory=list)  # ChordNode, TupletNode, or ContinuationNode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "beats": [b.to_dict() for b in self.beats]
        }


@dataclass
class RepeatMeasureNode:
    """Represents a measure repeat (% or %xN)."""
    type: str = "RepeatMeasure"
    count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "count": self.count
        }


@dataclass
class RepeatSectionNode:
    """Represents a repeat section (|: ... :|)."""
    type: str = "RepeatSection"
    measures: List[Any] = field(default_factory=list)  # MeasureNode or RepeatMeasureNode
    repeat_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "repeatCount": self.repeat_count,
            "measures": [m.to_dict() for m in self.measures]
        }


@dataclass
class MeasureLineNode:
    """Represents a line of measures."""
    type: str = "MeasureLine"
    measures: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "measures": [m.to_dict() for m in self.measures]
        }


@dataclass
class AnnotationNode:
    """Represents an annotation block."""
    type: str = "Annotation"
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content
        }


@dataclass
class SongNode:
    """Root AST node representing the entire song."""
    type: str = "Song"
    body: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "body": [node.to_dict() for node in self.body]
        }


class ChordParser:
    """
    Parses chord symbols into root, quality, and bass components.
    Fixes the spec issue where "Am" was shown as root="Am", quality="".
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
            chord_str: The chord symbol string

        Returns:
            ChordNode with parsed components
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
    """

    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a token stream.

        Args:
            tokens: List of tokens from the lexer
        """
        self.tokens = tokens
        self.position = 0

    def parse(self) -> SongNode:
        """
        Parse the token stream into an AST.

        Returns:
            SongNode representing the entire song
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
                    # If the next token (after |) is a newline/EOF, consume the |
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

        # Parse first measure content
        first_measure = MeasureNode(beats=self._parse_measure_content())
        section.measures.append(first_measure)

        # Parse additional measures within the repeat section
        while self._check(TokenType.BAR_START):
            self._advance()  # consume BAR_START

            if self._check(TokenType.SINGLE_REPEAT):
                section.measures.append(self._parse_repeat_measure())
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

    Args:
        input_text: The noten format string

    Returns:
        SongNode AST
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
