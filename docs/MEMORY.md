# 🧠 Project Memory 🧠

Preserved context, decisions, and direction.

---

## Current State (May 2026)

### StrulovitzGhost — Active Development (Stage 1: Single Machine)

**What works end-to-end:**
- Flask server (`src/app.py`) — 9 REST endpoints, all tested
- SQLite DB via SQLAlchemy (`src/models.py`) — Question → Tasks pipeline, 3-state status (pending/claimed/completed), MySQL-ready
- PyQt6 GUI (`src/gui.py`) — 3-mode unified app (Client/Boss/Worker), dark theme, QThread-based generation, model downloader buttons
- Local LLM scene splitting (`src/llm.py`) — Ollama or LM Studio, structured 6-layer JSON output
- Qwen-Image-2512 generation (`src/generator.py`) — diffusers pipeline with BnB 4-bit CPU offload (works on RTX 4070 Ti 12GB), also ComfyUI path with GGUF workflow
- Model downloader (`src/downloader.py`) — from HuggingFace with retry logic
- One-click setup (`setup.bat`) — Miniconda env, all packages, ComfyUI cloned

**Tests:**
- `test_api.py` — 17/17 E2E API tests passed (submit→split→claim→upload→complete)
- `test_e2e_real.py` — Full pipeline with REAL Qwen AI on Layer 4, passed
- `test_timing.py` — Progress bar benchmark with test-shot timing estimation, working
- `test_layer1.py`, `test_real_layer.py`, `test_scale.py`, `test_step_by_step.py`, `test_one.py` — various generation/quality tests

**Hardware:** RTX 4070 Ti 12GB — Qwen 4-bit generation works (~3 min per layer at 512×384 / 15 steps)

**Recent work direction (last session, interrupted by Ctrl+C):**
- Testing individual layer generation quality (Layer 1 foreground, Layer 4 mid-distance)
- Object scaling for depth illusion (100% near → 70% far)
- Realistic D&D scene generation with distance-based prompt engineering

### ⛔ CRITICAL RULES (May 18, 2026)

1. **NEVER download models without explicit permission.** HuggingFace `snapshot_download` filled 47 GB disk. Models are downloaded via GUI buttons only, never automatically by any script or test. Before any download, report size and ask.

2. **Conda env Python path:** `%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe` — always use this full path, never `conda run` (hangs in PowerShell).

3. **Any command that might write large amounts of data** (downloads, generations, cache writes) MUST be confirmed with user first.

4. **DO THE FULL JOB.** Never reward hack, never do a tiny part of what Nir asked, never ignore parts of the request, never do a half-ass job to save time. Complete everything asked.

### Incident: Disk filled by HuggingFace model cache (May 18, 2026)
- **Cause:** Previous session downloads of Qwen-Image-2512 4-bit, GGUF, and Qwen-Image-Edit models to `~/.cache/huggingface/hub/`
- **Size:** 47 GB
- **Status:** Cleared. Models NOT needed for development — only for actual generation runs initiated by user.
- **Prevention:** `downloader.py` must be modified to warn size before downloading. The `generate_diffusers()` function must NOT auto-download models — it should fail with a clear message if model not found.

### Key decisions made:
- All communication is polling-based via Flask (no WebSockets) — simpler, works over LAN/internet
- Workers generate independently, 6 separate Qwen runs (no cross-layer coordination)
- No cloud AI ever — local Qwen for both text splitting and image generation
- MySQL switch is a one-line config change (SQLAlchemy abstraction)
- ComfyUI bundled in repo for accessibility, but diffusers is default path

---

### Working package versions (from conda env, May 18 2026)
```
torch                2.12.0+cu126
torchvision          0.27.0+cu126
diffusers            0.39.0.dev0
transformers         5.8.1
accelerate           1.13.0
bitsandbytes         0.49.2
sentencepiece        0.2.1
```

### Model Inventory (May 18 2026 — Updated)
| Model | Size | Status |
|-------|------|--------|
| `unsloth/Qwen-Image-2512-unsloth-bnb-4bit` | ~13 GB | ✅ Downloaded |
| `unsloth/Qwen-Image-2512-GGUF` | ~13 GB | ✅ Downloaded (fixed filename: lowercase `qwen-image-2512-Q4_K_M.gguf`) |
| `blanchon/Qwen-Image-Edit-2509-bnb-4bit` | ~14 GB | ✅ Downloaded |
| ComfyUI | ~2 GB | ✅ Present at `src/comfyui/main.py` |
| Output PNGs | ~50 MB | ✅ 26 test images in `src/output/` |
| C: drive free | 32 GB | After all 3 model downloads |

### Fix: GGUF filename in downloader.py
- **Was:** `GGUF_FILE = "Qwen-Image-2512-Q4_K_S.gguf"` → 404
- **Fixed:** `GGUF_FILE = "qwen-image-2512-Q4_K_M.gguf"` → works

## BLOCKER — Torch broken, DLLs locked (Late Night May 18 2026)

### State at session end
- **All 3 AI models downloaded** (~40 GB total, 32 GB free on C:)
- **ComfyUI present** at `src/comfyui/main.py`
- **GGUF filename fixed** in `downloader.py` (lowercase)
- **Torch CANNOT import** — hangs silently with any timeout length
- **Torch DLLs CANNOT be deleted** — locked by running process (permission denied on every .dll/.pyd)

### What was tried and failed
1. `conda run` → hangs in PowerShell (known issue)
2. `import torch` → hangs, no output, any timeout (15-30s)
3. `import torch` with `CUDA_VISIBLE_DEVICES=""` → still hangs
4. `pip uninstall torch` → hangs, no output
5. `pip uninstall --verbose torch` → hangs, no output
6. `Remove-Item -Force` on torch dir → all .dll/.pyd files Access Denied (locked)
7. `pip install --force-reinstall torch==2.12.0+cu126` → hangs, no output

### Most likely cause
CUDA DLLs (`c10.dll`, `c10_cuda.dll`, `torch.dll`, `cudnn*.dll`, etc.) are locked by some process. Either:
- Zombie Python from a previous torch import
- ComfyUI background process
- Some other CUDA-using application

### What to try next (in order)
1. **Reboot PC** — unlocks all DLLs. Then reinstall torch:
   ```
   %USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe -m pip install torch==2.12.0+cu126 torchvision==0.27.0+cu126 --extra-index-url https://download.pytorch.org/whl/cu126
   ```
2. If reboot doesn't fix: **recreate conda env from scratch** using exact version pins below.
3. If still broken: run `setup.bat` fresh.

### Exact versions (from working state)
```
torch                2.12.0+cu126
torchvision          0.27.0+cu126
diffusers            0.39.0.dev0
transformers         5.8.1
accelerate           1.13.0
bitsandbytes         0.49.2
sentencepiece        0.2.1
flask                 (latest)
flask-sqlalchemy      (latest)
pyqt6                 (latest)
pillow                (latest)
requests              (latest)
python-dotenv         (latest)
rembg                 (latest)
```

### Conda env Python path (CRITICAL — always use this)
```
%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe
```
Never use `conda run` — it hangs in PowerShell.

### AI Models — How to download (already done, May 18)
All 3 models downloaded to `~/.cache/huggingface/hub/`. To verify:
```python
from downloader import check_model_cached
print(check_model_cached("unsloth/Qwen-Image-2512-unsloth-bnb-4bit"))  # True
print(check_model_cached("unsloth/Qwen-Image-2512-GGUF"))   # True
print(check_model_cached("blanchon/Qwen-Image-Edit-2509-bnb-4bit"))  # True
```
GGUF filename fixed in downloader.py: `qwen-image-2512-Q4_K_M.gguf` (lowercase!)

### Next task when env is fixed: Generate Layer 1
```
Prompt: Ghibli animation style. Tree branches left+right framing, owl on branch,
rabbit on root, drawn 20cm away, green screen bg, clean edges.
→ Qwen 4-bit diffusers, 15 steps @768×576 → rembg → scale 100% / center 60% → save
Est: ~4 min on RTX 4070 Ti
```
Full prompt in Layer Generation Pipeline section below.

### Successful commands (save for reference)
```
# Check GPU (fast)
%USERPROFILE%miniconda3\envs\strulovitzghost\python.exe -c "import torch; print(torch.cuda.get_device_name(0))"

# Download models (one at a time, ~10-15 min each, from src/ directory)
%USERPROFILE%miniconda3\envs\strulovitzghost\python.exe -c "exec(open('downloader.py').read()); download_diffusers_4bit()"
%USERPROFILE%miniconda3\envs\strulovitzghost\python.exe -c "exec(open('downloader.py').read()); download_comfyui_gguf()"
%USERPROFILE%miniconda3\envs\strulovitzghost\python.exe -c "exec(open('downloader.py').read()); download_qwen_image_edit()"

# Generate Layer 1 (when torch works)
%USERPROFILE%miniconda3\envs\strulovitzghost\python.exe -c "from generator import generate_diffusers; generate_diffusers('PROMPT HERE', 'output/layer1.png', width=768, height=576, num_steps=15, remove_bg=True)"

# Check disk
%USERPROFILE%miniconda3\envs\strulovitzghost\python.exe -c "import shutil; s=shutil.disk_usage('C:/'); print(f'Free: {s.free/1e9:.1f} GB')"

# Check if model cached
%USERPROFILE%miniconda3\envs\strulovitzghost\python.exe -c "from downloader import check_model_cached; print(check_model_cached('unsloth/Qwen-Image-2512-unsloth-bnb-4bit'))"
```

---

## Layer Generation Pipeline

### Layer 1 — Closest (20cm, 100% scale, center=60%)
**Prompt:**
```
Ghibli animation style.
Tree branch tips entering from LEFT and RIGHT edges, framing the scene like a window.
On one branch, an owl sits silently, watching.
On the ground at the BOTTOM, a thick tree root with detailed bark texture,
drawn as if viewed from VERY CLOSE, 20 centimeters away — large, textured, immersive.
A curious rabbit sits on the root, its back turned to the viewer, looking forward.
The ground is drawn from extremely close — detailed moss, grass blades, textures.
Green screen background in the center where the clearing view would be.
Clean edges. Isolated subjects.
```
**Pipeline:** Qwen 4-bit (diffusers) → 15 steps @768×576 → rembg BG removal → scale 100% / center 60% → save
**Est time:** ~4 min on RTX 4070 Ti | **Disk:** ~2 MB output

### Layer 2 — Mid-close (90% scale, center=55%)
Elf paladin girl + Human druid girl on fallen log, backs to viewer, gossiping, laughing, backpacks.

### Layer 3 — Mid (80% scale, center=50%)
Dwarf cleric guy + Halfling thief guy arguing over campfire with roasting pig, closer flowers.

### Layer 4 — Mid-far (70% scale, center=45%)
Tiefling fighter girl + Dragonborn wizard guy on rocks, mid flower patches. "20 meters away — grass smooth texture, flowers tiny dots."

### Layer 5 — Far background (N/A — no scaling)
Ancient magical oak forest, glowing motes, tree line around clearing, dark forest shadows.

### Layer 6 — Farthest background / sky (N/A — no scaling)
Night sky with stars and full moon, snow-capped mountains on horizon, subtle clouds, misty haze at mountain base.

### Scaling Formula (Layers 1–4)
| Layer | Scale % | Center % | Distance |
|-------|---------|----------|----------|
| 1     | 100     | 60       | 20 cm    |
| 2     | 90      | 55       | ~3 m     |
| 3     | 80      | 50       | ~10 m    |
| 4     | 70      | 45       | ~20 m    |

`center = 45 + (4 - layer) * 5` — higher center% = lower on canvas = closer to viewer. Farther layers shift up toward horizon.
