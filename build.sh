#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# AI Image Enhancer — Build Executable with PyInstaller
# Produces: dist/AIImageEnhancer
# ─────────────────────────────────────────────────────────────────────────────

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}ℹ  $1${NC}"; }
success() { echo -e "${GREEN}✓  $1${NC}"; }

VENV_DIR="$(pwd)/.venv"
[ -d "$VENV_DIR" ] && source "$VENV_DIR/bin/activate"

info "Installing PyInstaller …"
pip install pyinstaller>=6.6.0 --quiet

info "Building executable …"

pyinstaller \
    --name "AIImageEnhancer" \
    --onedir \
    --windowed \
    --noconfirm \
    --clean \
    --add-data "src:src" \
    --add-data "assets:assets" \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "cv2" \
    --hidden-import "PIL" \
    --hidden-import "numpy" \
    --hidden-import "torch" \
    --hidden-import "basicsr" \
    --hidden-import "realesrgan" \
    --hidden-import "gfpgan" \
    --hidden-import "diffusers" \
    --hidden-import "transformers" \
    --collect-all "basicsr" \
    --collect-all "facexlib" \
    --collect-all "gfpgan" \
    --collect-all "realesrgan" \
    main.py

success "Build complete → dist/AIImageEnhancer/"
echo ""
echo "  Run with:  ./dist/AIImageEnhancer/AIImageEnhancer"
echo ""
echo "  To create AppImage (optional):"
echo "    Install appimagetool and wrap dist/AIImageEnhancer/"
echo ""
