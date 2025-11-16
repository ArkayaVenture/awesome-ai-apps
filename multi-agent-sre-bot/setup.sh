#!/bin/bash
# Setup script for Multi-Agent SRE Bot

# Don't exit on error - we want to show all issues
# set -e

echo "🤖 Setting up Multi-Agent SRE Bot..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(python3 -c "import sys; print(sys.version_info.major)")
python_minor=$(python3 -c "import sys; print(sys.version_info.minor)")
echo "Python version: $python_version"

# Select requirements file based on Python version
if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 13 ]; then
    echo "⚠️  Python 3.13+ detected. Using requirements without memori."
    REQUIREMENTS_FILE="requirements-py313.txt"
else
    REQUIREMENTS_FILE="requirements.txt"
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies from $REQUIREMENTS_FILE..."
pip install --upgrade pip || echo "⚠️  pip upgrade failed, continuing..."
if ! pip install -r "$REQUIREMENTS_FILE"; then
    echo "⚠️  Some optional packages failed to install"
    echo "⚠️  The bot may still work with limited functionality"
    echo "⚠️  Continuing setup..."
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/vector_store
mkdir -p tmp

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one from .env.example"
    echo "   cp .env.example .env"
    echo "   Then edit .env with your credentials"
else
    echo "✅ .env file found"
fi

# Check for kubeconfig
if [ -z "$KUBECONFIG" ] && [ ! -f ~/.kube/config ]; then
    echo "⚠️  Kubernetes config not found. Please set KUBECONFIG or configure kubectl"
else
    echo "✅ Kubernetes config found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your .env file with API keys and credentials"
echo "2. Set K8S_PLATFORM environment variable (local, aws, azure, or gcp)"
echo "3. Run the bot:"
echo "   - CLI: python cli.py 'Your query here'"
echo "   - API: uvicorn api.main:app --reload"
echo "   - UI: streamlit run app.py"
echo ""

