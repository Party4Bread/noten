"""
Noten Lexer - Tokenizes chord chart input according to the LLM-Chart specification.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum, auto


class TokenType(Enum):
    """
    Token types as defined in Section 2.1 of the specification.

    Attributes:
        ANNOTATION_START: '{' - Starts an annotation.
        ANNOTATION_END: '}' - Ends an annotation.
        ANNOTATION_CONTENT: Content within an annotation block.
        BAR_START: '|' - Starts a measure (and ends previous one).
        BAR_END: '|' - Ends a measure (conceptually same as BAR_START).
        REPEAT_START: '|:' - Starts a repeat section.
        REPEAT_END: ':|' - Ends a repeat section.
        CHORD: Musical chord symbol (e.g., "C", "Am7").
        NO_CHORD: "N.C." - Indicates no chord played.
        CONTINUATION: '.' - Extends duration of previous chord.
        TUPLET_START: '(' - Starts a tuplet group.
        TUPLET_END: ')' - Ends a tuplet group.
        SINGLE_REPEAT: '%' - Repeats previous measure.
        MULTI_REPEAT: 'xN' or '%xN' - Repeats section or measure N times.
        NEWLINE: Line break character.
        WHITESPACE: Spaces or tabs.
    """
    ANNOTATION_START = auto()
    ANNOTATION_END = auto()
    ANNOTATION_CONTENT = auto()
    BAR_START = auto()
    BAR_END = auto()
    REPEAT_START = auto()
    REPEAT_END = auto()
    CHORD = auto()
    NO_CHORD = auto()
    CONTINUATION = auto()
    TUPLET_START = auto()
    TUPLET_END = auto()
    SINGLE_REPEAT = auto()
    MULTI_REPEAT = auto()
    NEWLINE = auto()
    WHITESPACE = auto()


@dataclass
class Token:
    """
    Represents a single token from the input.

    Attributes:
        type: The type of the token (e.g., CHORD, BAR_START).
        value: The raw string value of the token.
        line: The line number where the token appears (1-based).
        column: The column number where the token starts (1-based).
    """
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self):
        """
        Return a string representation of the token.

        Returns:
            String representation useful for debugging.
        """
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"


class NotenLexer:
    """
    Tokenizer for the Noten (LLM-Chart) format.

    Converts input string into a stream of tokens according to the
    specification in Section 2.1.

    Attributes:
        input_text: The original input string.
        tokens: The list of generated tokens.
        current_line: Current line number during scanning.
        current_column: Current column number during scanning.
    """

    # Token patterns in priority order (more specific patterns first)
    TOKEN_PATTERNS = [
        # Annotations (must come before individual braces)
        (r'\{[^}]+\}', None),  # Will be split into START, CONTENT, END

        # Repeat markers (must come before BAR_START/BAR_END)
        (r'\|:', TokenType.REPEAT_START),
        (r':\|', TokenType.REPEAT_END),

        # Multi-repeat (must come before SINGLE_REPEAT)
        (r'%?x\d+', TokenType.MULTI_REPEAT),

        # Single repeat
        (r'%', TokenType.SINGLE_REPEAT),

        # Bar markers
        (r'\|', TokenType.BAR_START),  # Also serves as BAR_END

        # No chord
        (r'N\.C\.', TokenType.NO_CHORD),

        # Tuplet markers
        (r'\(', TokenType.TUPLET_START),
        (r'\)', TokenType.TUPLET_END),

        # Continuation marker (must come after N.C. to avoid conflicts)
        (r'\.', TokenType.CONTINUATION),

        # Chord pattern: Root (A-G), optional accidental (#/b), quality/extensions
        (r'[A-G](?:#|b)?(?:[a-zA-Z0-9b#+°ø/])*', TokenType.CHORD),

        # Whitespace
        (r'[ \t]+', TokenType.WHITESPACE),

        # Newline
        (r'\n', TokenType.NEWLINE),
    ]

    def __init__(self, input_text: str):
        """
        Initialize the lexer with input text.

        Args:
            input_text: The noten format string to tokenize.
        """
        self.input_text = input_text
        self.tokens: List[Token] = []
        self.current_line = 1
        self.current_column = 1

    def tokenize(self) -> List[Token]:
        """
        Tokenize the entire input string.

        Iterates through the input text, matching patterns to generate tokens.
        Handles annotations by splitting them into component tokens.

        Returns:
            List[Token]: The list of generated tokens.

        Raises:
            ValueError: If an unexpected character is encountered.
        """
        position = 0

        while position < len(self.input_text):
            # Try to match each pattern
            matched = False

            for pattern, token_type in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.input_text, position)

                if match:
                    value = match.group(0)

                    # Special handling for annotations
                    if value.startswith('{') and value.endswith('}'):
                        self._add_annotation_tokens(value)
                    else:
                        # Regular token
                        token = Token(
                            type=token_type,
                            value=value,
                            line=self.current_line,
                            column=self.current_column
                        )
                        self.tokens.append(token)

                    # Update position and line/column tracking
                    position = match.end()
                    self._update_position(value)
                    matched = True
                    break

            if not matched:
                # Unknown character - raise error
                raise ValueError(
                    f"Unexpected character '{self.input_text[position]}' "
                    f"at line {self.current_line}, column {self.current_column}"
                )

        return self.tokens

    def _add_annotation_tokens(self, annotation: str):
        """
        Split annotation into START, CONTENT, END tokens.

        Args:
            annotation: The full annotation string including braces
        """
        # Add ANNOTATION_START '{'
        self.tokens.append(Token(
            type=TokenType.ANNOTATION_START,
            value='{',
            line=self.current_line,
            column=self.current_column
        ))
        self._update_position('{')

        # Add ANNOTATION_CONTENT (everything between braces)
        content = annotation[1:-1]
        self.tokens.append(Token(
            type=TokenType.ANNOTATION_CONTENT,
            value=content,
            line=self.current_line,
            column=self.current_column
        ))
        self._update_position(content)

        # Add ANNOTATION_END '}'
        self.tokens.append(Token(
            type=TokenType.ANNOTATION_END,
            value='}',
            line=self.current_line,
            column=self.current_column
        ))
        self._update_position('}')

    def _update_position(self, text: str):
        """
        Update line and column counters based on consumed text.

        Args:
            text: The text that was just consumed
        """
        for char in text:
            if char == '\n':
                self.current_line += 1
                self.current_column = 1
            else:
                self.current_column += 1

    def get_tokens(self, include_whitespace: bool = False) -> List[Token]:
        """
        Get the list of tokens, optionally filtering out whitespace.

        Args:
            include_whitespace: If False, WHITESPACE tokens are excluded from the result.
                                Defaults to False.

        Returns:
            List[Token]: The filtered list of tokens.
        """
        if include_whitespace:
            return self.tokens
        else:
            return [t for t in self.tokens if t.type != TokenType.WHITESPACE]


def tokenize(input_text: str, include_whitespace: bool = False) -> List[Token]:
    """
    Convenience function to tokenize noten input.

    Wraps the NotenLexer to provide a simple function call for tokenizing text.

    Args:
        input_text: The noten format string to be tokenized.
        include_whitespace: Whether to include whitespace tokens in the output list.
                            Defaults to False.

    Returns:
        List[Token]: A list of Token objects representing the input string.

    Raises:
        ValueError: If an unknown character is encountered.
    """
    lexer = NotenLexer(input_text)
    lexer.tokenize()
    return lexer.get_tokens(include_whitespace=include_whitespace)


if __name__ == '__main__':
    # Test the lexer with the example from the spec
    test_input = """{title: LLM-Chart Demo}
{key: C}
{time: 4/4}

{Verse 1}
| Cmaj7 . . G | (Am G F) C |
|: C | % :| x2
"""

    print("Testing Noten Lexer")
    print("=" * 60)
    print("Input:")
    print(test_input)
    print("\n" + "=" * 60)
    print("Tokens (without whitespace):\n")

    tokens = tokenize(test_input)
    for token in tokens:
        print(token)
