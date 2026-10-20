#!/usr/bin/env bash
# ==============================================================================
# PDF-ChatGPT - macOS Launcher
# Double-click this file in Finder to install (first run) and start the app.
# If macOS blocks it, right-click -> Open, or run:
#   chmod +x "Start App (Mac).command"
# ==============================================================================

set -uo pipefail
cd "$(dirname "$0")"

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

echo "==============================================================================="
echo "  PDF-ChatGPT - Enterprise RAG Application Launcher (Was made by Oleh Datsyk)"
echo "==============================================================================="
echo ""

fail() {
    echo -e "${RED}[ERROR]${RESET} $1"
    echo ""
    echo "Press Enter to close this window..."
    read -r
    exit 1
}

# ------------------------------------------------------------------
# 1. Check Python is installed
# ------------------------------------------------------------------
echo "[1/7] Checking for Python..."
PYTHON_BIN=""
for candidate in python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    fail "Python was not found. Install Python 3.12+ from https://www.python.org/downloads/ (or 'brew install python@3.12') and run this script again."
fi

PYVER=$("$PYTHON_BIN" --version 2>&1)
echo "      Found $PYVER ($PYTHON_BIN)"
echo ""

# ------------------------------------------------------------------
# 2. Create virtual environment if missing
# ------------------------------------------------------------------
echo "[2/7] Checking for virtual environment..."
if [ ! -f "venv/bin/activate" ]; then
    echo "      No virtual environment found. Creating one now..."
    "$PYTHON_BIN" -m venv venv || fail "Failed to create the virtual environment."
    echo "      Virtual environment created at ./venv"
else
    echo "      Virtual environment already exists."
fi
echo ""

# ------------------------------------------------------------------
# 3. Activate virtual environment
# ------------------------------------------------------------------
echo "[3/7] Activating virtual environment..."
# shellcheck disable=SC1091
source venv/bin/activate || fail "Failed to activate the virtual environment."
echo "      Activated."
echo ""

# ------------------------------------------------------------------
# 4. Install dependencies if missing
# ------------------------------------------------------------------
echo "[4/7] Checking dependencies..."
if ! python -c "import fastapi" >/dev/null 2>&1; then
    echo "      Installing dependencies from requirements.txt ..."
    echo "      This may take a few minutes on first run."
    pip install --upgrade pip >/dev/null
    pip install -r requirements.txt || fail "Dependency installation failed. See the messages above."
else
    echo "      Dependencies already installed."
fi
echo ""

# ------------------------------------------------------------------
# 5. Verify .env file exists
# ------------------------------------------------------------------
echo "[5/7] Checking for .env configuration file..."
if [ ! -f ".env" ]; then
    echo "      No .env file found. Creating one from .env.example ..."
    cp .env.example .env
    echo ""
    echo -e "  ${YELLOW}****************************************************************${RESET}"
    echo -e "  ${YELLOW}*  IMPORTANT: Open the new .env file and set your             *${RESET}"
    echo -e "  ${YELLOW}*  OPENAI_API_KEY before using chat features.                 *${RESET}"
    echo -e "  ${YELLOW}*  Get a key at https://platform.openai.com/api-keys          *${RESET}"
    echo -e "  ${YELLOW}****************************************************************${RESET}"
    echo ""
elif grep -q "OPENAI_API_KEY=sk-your-openai-api-key-here" .env; then
    echo ""
    echo -e "  ${YELLOW}[WARNING] OPENAI_API_KEY in .env still looks like the placeholder value.${RESET}"
    echo -e "  ${YELLOW}Chat and document indexing will fail until you set a real key.${RESET}"
    echo ""
else
    echo "      .env file found."
fi
echo ""

# ------------------------------------------------------------------
# 6. Ensure required folders exist
# ------------------------------------------------------------------
echo "[6/7] Ensuring required folders exist..."
mkdir -p data/uploads data/vector_store logs
echo "      Folders ready: data/uploads, data/vector_store, logs"
echo ""

# ------------------------------------------------------------------
# 7. Launch the application
# ------------------------------------------------------------------
echo "[7/7] Starting PDF-ChatGPT ..."
echo -e "      Once running, open ${BOLD}http://localhost:8000${RESET} in your browser."
echo "      Press CTRL+C in this window to stop the server."
echo "============================================================"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}[ERROR]${RESET} The application exited with an error (code $EXIT_CODE)."
    echo "Scroll up to review the messages above."
else
    echo -e "${GREEN}PDF-ChatGPT has stopped.${RESET}"
fi
echo ""
echo "Press Enter to close this window..."
read -r
