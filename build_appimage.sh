#!/bin/bash
# =============================================================================
# AI Image Enhancer — Full Build Script
# Creates a single-click AppImage for Ubuntu 24.04
#
# Usage:
#   bash build_appimage.sh
#
# Output:
#   AIImageEnhancer-x86_64.AppImage   ← double-click to run!
# =============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}  ►  $1${NC}"; }
success() { echo -e "${GREEN}  ✓  $1${NC}"; }
warn()    { echo -e "${YELLOW}  ⚠  $1${NC}"; }
error()   { echo -e "${RED}  ✗  $1${NC}"; exit 1; }
header()  { echo -e "\n${BOLD}${BLUE}═══  $1  ═══${NC}\n"; }

APP_NAME="AIImageEnhancer"
APP_VERSION="1.0.0"
VENV_DIR="$SCRIPT_DIR/.venv"
DIST_DIR="$SCRIPT_DIR/dist"
APPDIR="$SCRIPT_DIR/AppDir"
APPIMAGE_OUT="$SCRIPT_DIR/${APP_NAME}-x86_64.AppImage"

# =============================================================================
echo ""
echo -e "${BOLD}${BLUE}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   🤖  AI Image Enhancer — AppImage Builder  ║"
echo "  ║   Ubuntu 24.04 · Python 3.12 · PySide6      ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# =============================================================================
header "STEP 1: System Dependencies"

info "Updating apt and installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    python3-pip git wget curl \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    libgomp1 libfuse2 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 \
    libxkbcommon-x11-0 libdbus-1-3 \
    fonts-ubuntu patchelf binutils \
    2>/dev/null
success "System packages ready"

# =============================================================================
header "STEP 2: Python Virtual Environment"

if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment..."
    python3.12 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip wheel setuptools --quiet
success "Virtual environment: $VENV_DIR"

# =============================================================================
header "STEP 3: Install PyTorch"

if python -c "import torch; print(torch.__version__)" 2>/dev/null; then
    success "PyTorch already installed: $(python -c 'import torch; print(torch.__version__)')"
else
    GPU_FOUND=false
    command -v nvidia-smi &>/dev/null && GPU_FOUND=true

    if $GPU_FOUND; then
        warn "Installing GPU PyTorch (CUDA 12.1) — ~2.5 GB download..."
        pip install torch torchvision \
            --index-url https://download.pytorch.org/whl/cu121 \
            --quiet
    else
        warn "No GPU detected. Installing CPU PyTorch..."
        pip install torch torchvision \
            --index-url https://download.pytorch.org/whl/cpu \
            --quiet
    fi
    success "PyTorch installed"
fi

# =============================================================================
header "STEP 4: Install AI & GUI Dependencies"

info "Installing core packages..."
pip install \
    PySide6>=6.7.0 \
    Pillow>=10.3.0 \
    opencv-python-headless>=4.9.0 \
    numpy>=1.26.0 \
    scipy>=1.13.0 \
    tqdm requests packaging \
    huggingface_hub>=0.23.0 \
    einops timm \
    --quiet
success "Core packages installed"

info "Installing Real-ESRGAN + GFPGAN..."
pip install basicsr facexlib realesrgan gfpgan --quiet
success "Real-ESRGAN + GFPGAN installed"

info "Installing Diffusers ecosystem..."
pip install \
    diffusers>=0.27.0 \
    transformers>=4.40.0 \
    accelerate>=0.30.0 \
    safetensors>=0.4.3 \
    controlnet-aux>=0.0.7 \
    --quiet
success "Diffusers ecosystem installed"

info "Installing PyInstaller..."
pip install pyinstaller>=6.6.0 --quiet
success "PyInstaller ready"

# Optional xformers for GPU
if command -v nvidia-smi &>/dev/null; then
    info "Installing xFormers (GPU memory optimization)..."
    pip install xformers --quiet && success "xFormers installed" \
        || warn "xFormers skipped (optional)"
fi

# =============================================================================
header "STEP 5: PyInstaller Bundle"

info "Cleaning previous builds..."
rm -rf "$DIST_DIR" "$SCRIPT_DIR/build"

info "Running PyInstaller (this may take 5–10 minutes)..."
pyinstaller ai_enhancer.spec \
    --noconfirm \
    --clean \
    2>&1 | tail -20

BUNDLE="$DIST_DIR/$APP_NAME"
[ -d "$BUNDLE" ] || error "PyInstaller failed — no output in $BUNDLE"
success "Bundle created: $BUNDLE"

# =============================================================================
header "STEP 6: Create AppDir Structure"

info "Creating AppDir..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy bundle contents into AppDir
cp -r "$BUNDLE/." "$APPDIR/usr/bin/"

# App icon
ICON_SRC="$SCRIPT_DIR/assets/icons/app_icon.png"
if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$APPDIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
    cp "$ICON_SRC" "$APPDIR/${APP_NAME}.png"
fi

# ── AppRun script ──────────────────────────────────────────────────── #
cat > "$APPDIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
# AppImage entry point — sets up environment and launches app

SELF_DIR="$(dirname "$(readlink -f "$0")")"
export PATH="$SELF_DIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$SELF_DIR/usr/lib:$SELF_DIR/usr/bin:${LD_LIBRARY_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="$SELF_DIR/usr/bin/PySide6/Qt/plugins/platforms"
export QT_PLUGIN_PATH="$SELF_DIR/usr/bin/PySide6/Qt/plugins"

# Torch shared libraries
export LD_LIBRARY_PATH="$SELF_DIR/usr/bin/torch/lib:$LD_LIBRARY_PATH"

# Run the app
exec "$SELF_DIR/usr/bin/AIImageEnhancer" "$@"
APPRUN_EOF
chmod +x "$APPDIR/AppRun"

# ── Desktop file ───────────────────────────────────────────────────── #
cat > "$APPDIR/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Name=AI Image Enhancer
GenericName=Image Enhancer
Comment=Professional AI Image Upscaling and Restoration
Exec=AIImageEnhancer
Icon=${APP_NAME}
Type=Application
Categories=Graphics;Photography;
Keywords=AI;Image;Enhance;Upscale;Restore;
StartupWMClass=AIImageEnhancer
EOF

cp "$APPDIR/usr/share/applications/${APP_NAME}.desktop" "$APPDIR/${APP_NAME}.desktop"

success "AppDir structure created"

# =============================================================================
header "STEP 7: Download appimagetool & Create AppImage"

APPIMAGETOOL="$SCRIPT_DIR/appimagetool-x86_64.AppImage"

if [ ! -f "$APPIMAGETOOL" ]; then
    info "Downloading appimagetool..."
    wget -q --show-progress \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
    success "appimagetool downloaded"
fi

info "Building AppImage (this may take a few minutes)..."
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_OUT" 2>&1 | tail -10

chmod +x "$APPIMAGE_OUT"

# =============================================================================
header "STEP 8: Verify & Summary"

SIZE_MB=$(du -sh "$APPIMAGE_OUT" 2>/dev/null | cut -f1)
success "AppImage created!"

echo ""
echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════╗"
echo "║   ✅  BUILD SUCCESSFUL!                          ║"
echo "╠═══════════════════════════════════════════════════╣"
echo -e "║  File:  ${CYAN}$(basename "$APPIMAGE_OUT")${GREEN}"
echo -e "║  Size:  ${CYAN}$SIZE_MB${GREEN}"
echo "║                                                   ║"
echo "║  To run:                                          ║"
echo -e "║  ${CYAN}chmod +x AIImageEnhancer-x86_64.AppImage${GREEN}       ║"
echo -e "║  ${CYAN}./AIImageEnhancer-x86_64.AppImage${GREEN}              ║"
echo "║                                                   ║"
echo "║  Or double-click in file manager!                ║"
echo -e "╚═══════════════════════════════════════════════════╝${NC}"
echo ""
