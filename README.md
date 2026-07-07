# AI Image Enhancer — Professional Edition

> **Production-ready desktop application** for AI-powered image upscaling, restoration, and enhancement — running **entirely offline** on Ubuntu 24.04.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **AI Upscaling** | Real-ESRGAN, SwinIR, SUPIR, SDXL, ControlNet Tile, Flux Fill |
| **Upscale Targets** | 2K, 4K, 8K, 2×, 4× |
| **Face Restoration** | GFPGAN v1.4 — eyes, skin, hair |
| **Post-Processing** | Adaptive sharpen, CLAHE, smart denoise, edge enhance |
| **Batch Processing** | Entire folders with pause/resume/stop |
| **GPU Support** | Auto-detects CUDA, falls back to CPU |
| **Formats** | JPG, PNG, WEBP, BMP, TIFF input → PNG/JPEG/WEBP output |
| **Filename Handling** | **Preserves original filename exactly** — no suffixes added |

---

## 🗂 Project Structure

```
toolstransimage/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── install.sh                       # Auto-installer
├── build.sh                         # PyInstaller build
├── README.md
│
├── src/
│   ├── core/
│   │   ├── settings.py              # QSettings persistence
│   │   ├── logger.py                # Rotating file + colored console log
│   │   ├── gpu_detector.py          # CUDA auto-detection
│   │   └── image_utils.py           # I/O utilities
│   │
│   ├── models/
│   │   ├── base_model.py            # Abstract base class
│   │   ├── real_esrgan_model.py     # Real-ESRGAN 4x
│   │   ├── swinir_model.py          # SwinIR
│   │   ├── sdxl_model.py            # Stable Diffusion XL Img2Img
│   │   ├── supir_model.py           # SUPIR
│   │   ├── controlnet_model.py      # ControlNet Tile
│   │   ├── flux_model.py            # Flux Fill
│   │   └── face_restore_model.py    # GFPGAN
│   │
│   ├── pipeline/
│   │   ├── processor.py             # Main pipeline orchestrator
│   │   └── postprocessing.py        # OpenCV post-processing
│   │
│   ├── gui/
│   │   ├── main_window.py           # Main window
│   │   ├── styles.py                # Dark QSS theme
│   │   ├── panels/
│   │   │   ├── settings_panel.py    # AI settings sidebar
│   │   │   └── progress_panel.py    # Progress + log
│   │   └── widgets/
│   │       ├── image_preview.py     # Before/after split view
│   │       └── file_queue.py        # Image queue list
│   │
│   └── workers/
│       └── enhancement_worker.py    # QThread background processor
│
├── assets/
├── models_cache/                    # AI model weights (auto-downloaded)
└── logs/                            # Processing logs
```

---

## 🤖 AI Models

### Mode 1 — Real-ESRGAN *(Fast & Reliable)*
- Best for: General photos, portraits, landscapes
- VRAM: **4 GB+** (or CPU)
- Model auto-downloads on first use (~64 MB)

### Mode 2 — SwinIR *(High Detail)*
- Best for: Recovering fine textures
- VRAM: **6 GB+** (or CPU)

### Mode 3 — SUPIR *(Photorealistic)*
- Best for: Maximum quality, real-world photos
- VRAM: **12 GB+** required

### Mode 4 — SDXL Img2Img *(Creative Textures)*
- Best for: Adding AI-generated texture on top of upscaled images
- VRAM: **8 GB+** required
- Model: ~7 GB download on first use

### Mode 5 — ControlNet Tile *(Ultra Detail)*
- Best for: Architecture, fabric, complex textures
- VRAM: **10 GB+** required

### Mode 6 — Flux Fill *(State-of-the-Art)*
- Best for: Maximum detail, modern architecture
- VRAM: **12 GB+** required

### Mode 7 — ✨ Hybrid *(Recommended)*
- Pipeline: Real-ESRGAN → optional SDXL texture pass → Post-processing
- Adapts to available VRAM automatically

---

## 📦 Installation & Setup

### 🐧 On Ubuntu (Linux)

#### Quick Install:
```bash
cd toolstransimage
bash install.sh
```

#### Running:
```bash
./run.sh
```

---

### 🪟 On Windows

#### Prerequisites:
1. Download and install [Python 3.10 or 3.12](https://www.python.org/downloads/) (Make sure to check the box **"Add Python to PATH"** during installation).
2. Download and install [git](https://git-scm.com/downloads) (optional, or download this repository as a ZIP).

#### Quick Install & Run:
1. Extract the downloaded ZIP file of the repository.
2. Double-click the file **`build_windows.bat`**.
   - This script will check for Python, set up a virtual environment `.venv`, auto-detect if you have an NVIDIA GPU (to install CUDA 12.1 PyTorch) or CPU, and install all required libraries.
   - Finally, it will compile and output the Windows executable `.exe` inside `dist/AIImageEnhancer/`.

#### Manual Install (Command Line):
1. Open PowerShell or Command Prompt in the project folder:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install PyTorch:
   - For NVIDIA GPU (CUDA 12.1):
     ```cmd
     pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
     ```
   - For CPU-only:
     ```cmd
     pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
     ```
3. Install other requirements:
   ```cmd
   pip install -r requirements.txt
   ```
4. Run the app:
   ```cmd
   python main.py
   ```

---
---

## 🚀 Usage

```bash
# Activate venv and run
source .venv/bin/activate
python main.py

# Or use the launcher
./run.sh
```

### Steps
1. Click **Add Image** or **Add Folder**
2. Select **Output Folder**
3. Choose **AI Mode** in the left panel
4. Adjust **Post-Processing** sliders
5. Click **▶ Start Processing**
6. Watch real-time progress; output folder opens automatically when done

---

## 🏗 Build Executable

### On Windows (.exe):
1. Activate virtual environment:
   ```cmd
   .venv\Scripts\activate
   ```
2. Build executable using PyInstaller spec file:
   ```cmd
   pyinstaller ai_enhancer.spec
   ```
   - The standalone folder containing the executable will be output in: `dist/AIImageEnhancer/`
   - Double-click **`AIImageEnhancer.exe`** to run.

### On Ubuntu (Linux binary):
```bash
bash build.sh
# Output: dist/AIImageEnhancer/
./dist/AIImageEnhancer/AIImageEnhancer
```

---

## ⚙️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 | Ubuntu 24.04 |
| Python | 3.11 | 3.12 |
| RAM | 8 GB | 16 GB+ |
| GPU | Any NVIDIA (4 GB VRAM) | RTX 3080+ (10 GB+) |
| Disk | 10 GB | 50 GB (all models) |

---

## 📋 Filename Handling

> ✅ **Original filenames are always preserved.**

| Input | Output |
|-------|--------|
| `photo001.jpg` | `photo001.png` *(format changed)* |
| `IMG_1234.jpeg` | `IMG_1234.png` |
| `landscape.png` | `landscape.png` |

No `_enhanced`, `_upscaled`, `_final`, or timestamps are added.

---

## 📄 License

MIT License — free for personal and commercial use.
