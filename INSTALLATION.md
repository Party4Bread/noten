# Installation Guide

## Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install noten package

#### Development Installation (Editable Mode)

For local development where changes to the source code are immediately reflected:

```bash
# Create and activate a virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
uv pip install -e .
```

#### Install with Optional Dependencies

```bash
# Install with demo dependencies (litellm, anthropic, openai)
uv pip install -e ".[demo]"

# Install with dev dependencies (pytest)
uv pip install -e ".[dev]"

# Install with all optional dependencies
uv pip install -e ".[demo,dev]"
```

#### Production Installation

```bash
uv pip install noten  # (once published to PyPI)
```

### Running Tests

```bash
# Using the virtual environment Python
.venv/bin/python test_noten.py

# Or if venv is activated
python test_noten.py
```

### Running Demos

```bash
# Basic demo (no external dependencies required)
.venv/bin/python demo_reharmonization.py

# Real LLM demo (requires API keys)
.venv/bin/python demo_real_llm.py
```

## Using pip (Traditional)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# With optional dependencies
pip install -e ".[demo,dev]"
```

## Package Structure

```
noten/
├── pyproject.toml           # Package metadata and dependencies
├── src/
│   └── noten/              # Main package
│       ├── __init__.py     # Package exports
│       ├── noten_lexer.py  # Tokenizer
│       ├── noten_parser.py # Parser & AST
│       └── noten_rhythm.py # Rhythm calculation
├── test_noten.py           # Test suite
├── test_examples.py        # Example file tests
├── demo_reharmonization.py # Demo with simulated LLM
└── demo_real_llm.py        # Demo with real LLM APIs
```

## Usage

```python
from noten import parse, calculate_durations, print_rhythm_analysis

# Parse a chord progression
noten_input = """
{title: My Song}
{key: C}
{time: 4/4}

| C . . G | Am . F . |
"""

# Parse and analyze
ast = parse(noten_input)
events = calculate_durations(ast.to_dict())
print_rhythm_analysis(events)
```

## Dependencies

### Core (No Dependencies)
The core noten package has zero external dependencies - it uses only Python standard library.

### Optional Dependencies

- **demo**: For LLM integration demos
  - `litellm>=1.0.0` - Unified LLM API interface
  - `python-dotenv>=1.0.0` - Environment variable management
  - `anthropic>=0.25.0` - Anthropic Claude API
  - `openai>=1.0.0` - OpenAI API

- **dev**: For development and testing
  - `pytest>=7.0.0` - Testing framework

## Environment Variables

For LLM demos, create a `.env` file with your API keys:

```bash
# At least one of these is required for demo_real_llm.py
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```
