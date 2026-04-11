#!/bin/bash
# faster-whisper setup script for Windows (Git Bash/MSYS2)
# Uses existing ffmpeg at F:/依赖/ffmpeg/ffmpeg-8.1-essentials_build

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
FFMPEG_PATH="/f/依赖/ffmpeg/ffmpeg-8.1-essentials_build/bin"

echo "=========================================="
echo "  Faster Whisper Setup (Windows)"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python 3 not found"
    exit 1
fi

echo "[OK] Python version: $(python3 --version)"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[Setup] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "[OK] Virtual environment ready"

# Activate and install
echo "[Setup] Installing dependencies..."
source "$VENV_DIR/Scripts/activate"
pip install -q --upgrade pip
pip install -q faster-whisper

echo "[OK] Dependencies installed"

# Create wrapper script that includes ffmpeg in PATH
cat > "$SCRIPT_DIR/transcribe.bat" << 'EOF'
@echo off
setlocal EnableDelayedExpansion

set "FFMPEG_PATH=F:\依赖\ffmpeg\ffmpeg-8.1-essentials_build\bin"
set "PATH=%FFMPEG_PATH%;%PATH%"

set "SCRIPT_DIR=%~dp0"
set "PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"
set "TRANSCRIBE_SCRIPT=%SCRIPT_DIR%scripts\transcribe.py"

"%PYTHON%" "%TRANSCRIBE_SCRIPT%" %*
EOF

echo "[OK] Created transcribe.bat wrapper"

# Test ffmpeg
echo "[Test] Testing ffmpeg..."
if "$FFMPEG_PATH/ffmpeg.exe" -version > /dev/null 2>&1; then
    echo "[OK] ffmpeg working"
else
    echo "[Error] ffmpeg test failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Usage:"
echo "  .\\transcribe.bat audio.mp3"
echo "  .\\transcribe.bat audio.mp3 --language zh"
echo ""
