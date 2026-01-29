#!/bin/bash
# Quick-start script for running Blindfold Python SDK examples

set -e

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║              Blindfold Python SDK - Quick Start Script                   ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if API key is set
if [ -z "$BLINDFOLD_API_KEY" ]; then
    echo "⚠️  BLINDFOLD_API_KEY environment variable not set"
    echo ""
    echo "To get an API key:"
    echo "  1. Login to http://localhost:8000"
    echo "  2. Go to Settings → API Keys"
    echo "  3. Generate a new API key"
    echo "  4. Run: export BLINDFOLD_API_KEY=your-key"
    echo ""
    read -p "Do you want to enter your API key now? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your API key: " api_key
        export BLINDFOLD_API_KEY="$api_key"
        echo "✅ API key set for this session"
    else
        echo "❌ API key required. Exiting."
        exit 1
    fi
fi

# Check if backend is running
echo "🔍 Checking if backend is running..."
if curl -s http://localhost:8000/api/public/v1/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not responding at http://localhost:8000"
    echo ""
    echo "To start the backend:"
    echo "  cd backend"
    echo "  python -m uvicorn main:app --reload"
    echo ""
    exit 1
fi

# Install SDK if needed
echo ""
echo "📦 Checking SDK installation..."
if python3 -c "import blindfold" 2>/dev/null; then
    echo "✅ SDK is installed"
else
    echo "⚠️  SDK not installed. Installing..."
    pip install -e . > /dev/null 2>&1
    echo "✅ SDK installed"
fi

# Run the example
echo ""
echo "🚀 Running basic synchronous example..."
echo ""
python3 examples/basic_sync.py

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                           Example Complete!                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  • Try the async example: python3 examples/basic_async.py"
echo "  • Check examples/README.md for more information"
echo "  • Read the SDK documentation in README.md"
echo "  • Explore the Public API docs at backend/PUBLIC_API_DOCS.md"
echo ""
