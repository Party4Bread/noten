# LLM parseable Chord progression

## 1. Introduction & Goals

### 1.1. Purpose

This document specifies the syntax and grammar for the **LLM-Chart** format, a text-based musical chord notation system designed for efficient processing by Large Language Models (LLMs).

### 1.2. Design Principles

- **Unambiguous:** The grammar eliminates guesswork in aligning chords with rhythm.
- **Token-Efficient:** The syntax is concise to minimize context window usage.
- **Human-Readable:** The format remains intuitive for musicians to read and write.
- **Structurally Agnostic:** The format uses free-form annotations (`{...}`) for metadata and structure, rather than enforcing a rigid hierarchy like "verse" or "chorus".

## 2\. Lexical Analysis (Lexer)

The lexer's role is to convert the input string into a stream of tokens.

### 2.1. Token Definitions

|  |  |  |  |
| --- | --- | --- | --- |
| **Token Type** | **Lexeme Examples** | **Regex Pattern** | **Description** |
| `ANNOTATION_START` | `{` | `\\{` | Start of an annotation block. |
| `ANNOTATION_END` | `}` | `\\}` | End of an annotation block. |
| `ANNOTATION_CONTENT` | `key: C`, `Verse 1`, `Guitar Solo` | `[^}]+` | The raw string content inside an annotation. |
| `BAR_START` | \` | \` | `\|` |
| `BAR_END` | \` | \` | `\|` |
| `REPEAT_START` | \` | :\` | `\|:` |
| `REPEAT_END` | \`: | \` | `:\|` |
| `CHORD` | `C`, `G/B`, `Am7`, `Bm7b5` | \`\[A-G\](?:# | b)?\[a-zA-Z0-9b#+°ø/\]\*\` |
| `NO_CHORD` | `N.C.` | `N\\.C\\.` | Represents "No Chord". |
| `CONTINUATION` | `.` | `\\.` | A continuation marker, extending the previous chord. |
| `TUPLET_START` | `(` | `\\(` | Marks the beginning of a tuplet group. |
| `TUPLET_END` | `)` | `\\)` | Marks the end of a tuplet group. |
| `SINGLE_REPEAT` | `%` | `%` | Repeats the previous single measure. |
| `MULTI_REPEAT` | `%x3`, `x4` | `(?:%?x\\d+)\\b` | Repeats a measure or section multiple times. |
| `NEWLINE` | `\\n` | `\\n` | A newline character. |
| `WHITESPACE` | , `\\t` | `[ \\t]+` | One or more spaces or tabs (often ignored). |

### 2.2. Rhythmic Interpretation Rules

The `{time: ...}` annotation governs rhythm. The following rules clarify how duration is allocated.

1. **Beat Division**: Time within a measure is divided equally among its top-level elements. These elements are chords, tuplets, or continuation markers (`.`).
2. **Continuation Marker (`.`):** The `.` marker acts as a placeholder. Its calculated duration is assigned to the most recent preceding chord.
    - **Example in 4/4:** `| C . . G |` has four elements. Each gets 1 beat. `C` gets its beat plus the 2 from the dots, for a total duration of 3 beats. `G` gets 1 beat.
    - **Example in 4/4:** `| C . G |` has three elements. Each gets 4/3 beats. `C` gets its duration plus the dot's, for a total of 8/3 beats. `G` gets 4/3 beats.
3. **Tuplet (`(...)`):** A tuplet is a single top-level element. The chords *inside* the tuplet are played equally within the duration assigned to the tuplet as a whole.
    - **Example in 4/4:** `| C (G F G) |` has two top-level elements (`C` and `(G F G)`). Each gets 2 beats. The `G F G` chords are played as a triplet, each lasting 2/3 of a beat, within the final 2 beats of the measure.

## 3\. Syntactic Analysis (Parser)

The parser consumes the token stream to build an Abstract Syntax Tree (AST).

### 3.1. Grammar

```
<song> ::= (<annotation_line> | <measure_line>)*

<annotation_line> ::= ANNOTATION_START ANNOTATION_CONTENT ANNOTATION_END NEWLINE

<measure_line> ::= (<measure> | <repeat_section>)+ NEWLINE

<measure> ::= BAR_START <measure_content> BAR_END
            | BAR_START <measure_content> BAR_END MULTI_REPEAT
            | SINGLE_REPEAT
            | SINGLE_REPEAT MULTI_REPEAT

<measure_content> ::= (<beat_marker> WHITESPACE?)*

<repeat_section> ::= REPEAT_START <measure_content> (BAR_END BAR_START <measure_content>)* REPEAT_END
                   | REPEAT_START <measure_content> (BAR_END BAR_START <measure_content>)* REPEAT_END MULTI_REPEAT

<beat_marker> ::= <chord_entity> | <tuplet> | CONTINUATION

<chord_entity> ::= CHORD | NO_CHORD

<tuplet> ::= TUPLET_START (<chord_entity> WHITESPACE?)+ TUPLET_END

```

## 4\. Abstract Syntax Tree (AST)

The parser's output should be a structured object (e.g., JSON) representing the entire song.

### 4.1. AST Structure

The song's body is a flat list containing `Annotation` and `MeasureLine` nodes. Global metadata (like `key` or `time`) should be extracted by post-processing the `Annotation` nodes.

```
{
  "type": "Song",
  "body": [
    {
      "type": "Annotation | MeasureLine",
      // ... node-specific content ...
    }
  ]
}

```

### 4.2. Node Types

- **`Song`**: The root node.
- **`Annotation`**: A block of text for metadata, comments, or structural labels.
    - `type: "Annotation"`
    - `content: String` (The raw text from between the braces).
- **`MeasureLine`**: A single line of one or more measures.
- **`Measure`**: A standard measure containing beat markers.
    - `beats: [BeatMarker]`
- **`RepeatMeasure`**: A single (`%`) or multi (`%xN`) measure repeat.
    - `count: Number`
- **`RepeatSection`**: A multi-measure repeat (`|: ... :| xN`).
    - `measures: [Measure]`
    - `repeatCount: Number`
- **`BeatMarker`**: Can be one of `Chord`, `Tuplet`, or `Continuation`.
- **`Chord`**: A single chord.
    - `type: "Chord"`
    - `root: String`
    - `quality: String`
    - `bass: String | null`
- **`Tuplet`**: A group of chords played within a specified duration.
    - `type: "Tuplet"`
    - `chords: [Chord]`
- **`Continuation`**: A marker that extends the previous chord.
    - `type: "Continuation"`

## 5\. Full Example

### 5.1. Input Chart

```
{title: LLM-Chart Demo}
{key: C}
{time: 4/4}

{Verse 1}
| Cmaj7 . . G | (Am G F) C |
|: C | % :| x2

```

### 5.2. Parser Output (Final AST)

```
{
  "type": "Song",
  "body": [
    { "type": "Annotation", "content": "title: LLM-Chart Demo" },
    { "type": "Annotation", "content": "key: C" },
    { "type": "Annotation", "content": "time: 4/4" },
    { "type": "Annotation", "content": "Verse 1" },
    {
      "type": "MeasureLine",
      "measures": [
        {
          "type": "Measure",
          "beats": [
            { "type": "Chord", "root": "C", "quality": "maj7", "bass": null },
            { "type": "Continuation" },
            { "type": "Continuation" },
            { "type": "Chord", "root": "G", "quality": "", "bass": null }
          ]
        },
        {
          "type": "Measure",
          "beats": [
            {
              "type": "Tuplet",
              "chords": [
                { "root": "Am", "quality": "", "bass": null },
                { "root": "G", "quality": "", "bass": null },
                { "root": "F", "quality": "", "bass": null }
              ]
            },
            { "type": "Chord", "root": "C", "quality": "", "bass": null }
          ]
        }
      ]
    },
    {
      "type": "MeasureLine",
      "measures": [
        {
          "type": "RepeatSection",
          "repeatCount": 2,
          "measures": [
            {
              "type": "Measure",
              "beats": [
                { "type": "Chord", "root": "C", "quality": "", "bass": null }
              ]
            },
            { "type": "RepeatMeasure", "count": 1 }
          ]
        }
      ]
    }
  ]
}

```
