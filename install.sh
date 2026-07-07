#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# AI Image Enhancer — Ubuntu 24.04 Installation Script
# Run: bash install.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}ℹ  $1${NC}"; }
success() { echo -e "${GREEN}✓  $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠  $1${NC}"; }
error()   { echo -e "${RED}✗  $1${NC}"; exit 1; }

PYTHON_MIN="3.12"
VENV_DIR="$(pwd)/.venv"

echo ""
echo "════════════════════════════════════════════════════"
echo "  🤖 AI Image Enhancer — Installation Script"
echo "════════════════════════════════════════════════════"
echo ""

# ── System dependencies ──────────────────────────────────────────────── #
info "Installing system dependencies …"
sudo apt-get update -qq
sudo apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    python3-pip \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    libgomp1 \
    git wget curl \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 \
    libxkbcommon-x11-0 libdbus-1-3 \
    fonts-ubuntu
success "System dependencies installed"

# ── Python virtual environment ───────────────────────────────────────── #
info "Creating Python virtual environment in .venv …"
python3.12 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip wheel setuptools
success "Virtual environment created"

# ── Detect GPU ───────────────────────────────────────────────────────── #
GPU_FOUND=false
if command -v nvidia-smi &>/dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | sed 's/.*CUDA Version: //' | sed 's/ .*//')
    info "NVIDIA GPU detected — CUDA $CUDA_VERSION"
    GPU_FOUND=true
fi

# ── Install PyTorch ──────────────────────────────────────────────────── #
info "Installing PyTorch …"
if $GPU_FOUND; then
    warn "Installing GPU version (CUDA 12.1) — this may take a few minutes"
    pip install torch torchvision \
        --index-url https://download.pytorch.org/whl/cu121 \
        --quiet
else
    warn "No GPU detected — installing CPU-only PyTorch"
    pip install torch torchvision \
        --index-url https://download.pytorch.org/whl/cpu \
        --quiet
fi
success "PyTorch installed"

# ── Core dependencies ─────────────────────────────────────────────────── #
info "Installing core dependencies …"
pip install \
    PySide6>=6.7.0 \
    Pillow>=10.3.0 \
    opencv-python-headless>=4.9.0 \
    numpy>=1.26.0 \
    scipy>=1.13.0 \
    tqdm requests packaging huggingface_hub einops timm \
    --quiet
success "Core dependencies installed"

# ── Real-ESRGAN & Face Restore ────────────────────────────────────────── #
info "Installing Real-ESRGAN, GFPGAN …"
pip install basicsr facexlib realesrgan gfpgan --quiet
success "Real-ESRGAN & GFPGAN installed"

# ── Diffusers ecosystem ───────────────────────────────────────────────── #
info "Installing Diffusers, Transformers, Accelerate …"
pip install diffusers>=0.27.0 transformers>=4.40.0 accelerate>=0.30.0 safetensors>=0.4.3 --quiet
success "Diffusers ecosystem installed"

# ── ControlNet Aux ────────────────────────────────────────────────────── #
info "Installing ControlNet Aux …"
pip install controlnet-aux>=0.0.7 --quiet
success "ControlNet Aux installed"

# Optional xformers for GPU users
if $GPU_FOUND; then
    info "Installing xFormers (memory-efficient attention) …"
    pip install xformers --quiet && success "xFormers installed" || warn "xFormers install failed (optional)"
fi

# ── Create launcher script ────────────────────────────────────────────── #
LAUNCH_SCRIPT="$(pwd)/run.sh"
cat > "$LAUNCH_SCRIPT" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
cd "$SCRIPT_DIR"
python main.py "$@"
EOF
chmod +x "$LAUNCH_SCRIPT"
success "Launcher created: ./run.sh"

# ── Create .desktop file ─────────────────────────────────────────────── #
DESKTOP_FILE="$HOME/.local/share/applications/ai-image-enhancer.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=AI Image Enhancer
Comment=Professional AI Image Upscaling
Exec=$(pwd)/run.sh
Icon=$(pwd)/assets/icons/app_icon.png
Terminal=false
Type=Application
Categories=Graphics;Photography;
EOF
success "Desktop shortcut created"

# ── Summary ───────────────────────────────────────────────────────────── #
echo ""
echo "════════════════════════════════════════════════════"
echo "  ✅  Installation Complete!"
echo "════════════════════════════════════════════════════"
echo ""
echo "  To run the app:"
echo "    ./run.sh"
echo ""
echo "  Or activate venv manually:"
echo "    source .venv/bin/activate"
echo "    python main.py"
echo ""
