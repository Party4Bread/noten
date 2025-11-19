#!/bin/bash
# Quick script to run the noten LLM demo

echo "🎵 Noten LLM Demo Runner"
echo "======================="
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate venv
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import litellm" 2>/dev/null; then
    echo "Installing dependencies..."
    uv pip install litellm python-dotenv
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: No .env file found!"
    echo "Please create a .env file with at least one API key:"
    echo ""
    echo "ANTHROPIC_API_KEY=sk-ant-..."
    echo "OPENAI_API_KEY=sk-..."
    echo "GEMINI_API_KEY=AIza..."
    echo "OPENROUTER_API_KEY=sk-or-v1-..."
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Run the demo
echo ""
echo "Running demo..."
echo ""
python demo_real_llm.py
