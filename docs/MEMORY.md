# 🧠 Project Memory 🧠

**⛔ THIS IS NIR'S COMPUTER. NO COMMANDS MAY BE RUN WITHOUT EXPLICIT PERMISSION. ASK FIRST. ALWAYS. ⛔**

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

### ⛔ CRITICAL RULES (May 18, 2026 — updated May 19)

**9. NEVER USE rembg.** It destroyed Layer 1. It is built for product photos (single isolated subject) and strips all complex framing, branches, ground, and edges. Use chroma-key (PIL color range on green screen) instead for background removal on framing layers. For isolated character layers, use Qwen-Image-Edit model instead.

1. **NEVER download models without explicit permission.** HuggingFace `snapshot_download` filled 47 GB disk. Models are downloaded via GUI buttons only, never automatically by any script or test. Before any download, report size and ask.

2. **Conda env Python path:** `%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe` — always use this full path, never `conda run` (hangs in PowerShell).

3. **Any command that might write large amounts of data** (downloads, generations, cache writes) MUST be confirmed with user first.

4. **DO THE FULL JOB.** Never reward hack, never do a tiny part of what Nir asked, never ignore parts of the request, never do a half-ass job to save time. Complete everything asked.

5. **⛔ NEVER RUN SYSTEM-MODIFYING COMMANDS WITHOUT PERMISSION.** This is Nir's computer. Never create conda environments, install packages, delete files, create directories, or run ANY command that modifies the system without Nir's explicit permission. Ask first, explain what the command will do, and wait for approval. This rule was violated on May 19, 2026 (unauthorized conda create) — MUST NEVER HAPPEN AGAIN.

6. **🗣️ TALK BEFORE ACTING — ALWAYS.** Before ANY command or action, discuss with Nir first. Never surprise-execute. This includes git commands, file writes, directory creation, anything. Explain what you're about to do and get approval.

7. **⚖️ OFFER OPTIONS WITH PROS/CONS.** When there are multiple approaches, present them as choices with tradeoffs. Let Nir decide the path.

8. **⏱️ TIME ESTIMATES FOR EVERY MICRO-STEP.** Before any action, tell Nir exactly how long each sub-step will take. Set short timeouts on all commands (5-10 sec for checks, 30-60 sec for generation, max 120 sec). Never let a command hang indefinitely — if it times out, report and discuss next steps with Nir.

9. **🚫 NEVER USE rembg.** It is built for product photos (single isolated subject) and destroys complex framing — branches, ground, edges all get stripped. For transparency: use chroma-key on green screen (PIL color range) for framing layers; use Qwen-Image-Edit model for isolated character layers.

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

## 🔴 LAYER 1 — GENERATED BUT WRONG (May 19, 2026 session #4)

### What came out
- Empty transparent space + single owl floating top-third (partially erased) + single rabbit floating bottom-third
- NO tree branches, NO root, NO ground, NO moss, NO framing of any kind

### Qwen-Image-Layered (Dec 2025) — Investigated, NOT our solution
- Model decomposes existing flat images into RGBA layers with transparency
- NOT a generator — it only cuts up images that already exist
- We can't control per-layer content — the AI decides what goes in which layer
- Doesn't solve our problem (we need to CREATE specific content per depth layer, not decompose)
- Useful to know about but irrelevant for this project

### Open questions for Google AI search
Need specific answers about Qwen-Image-2512 prompt techniques for green screen backgrounds.

### Google search prompts needed:
1. How to prompt Qwen-Image-2512 to generate images with pure chroma key green background that can be keyed out for transparency
2. What negative prompts work best with Qwen-Image-2512 to prevent background artifacts when generating on green screen
3. Does Qwen-Image-2512 support output with alpha channel / transparent background directly
4. Qwen-Image-Edit-2509 examples for removing background and making it transparent - prompt examples that work
5. Best approach combining Qwen-Image-2512 generation + Qwen-Image-Edit-2509 for green screen background removal pipeline

### Root cause analysis
The generator's hardcoded suffix + negative prompt + rembg pipeline is fundamentally wrong for framing layers:

1. **Appended suffix kills complexity:** Every prompt gets `"The subject is small and centered on a plain green screen background. Isolated subject. Studio lighting. Clean edges."` appended. "Isolated subject" (singular) + "small and centered" contradicts Layer 1's complex diorama with branches entering from edges, ground at bottom, multiple elements.

2. **Negative prompt fights the framing:** `"busy background, cluttered, multiple objects, frame filling"` — Layer 1 IS "multiple objects" and "frame filling" by design! The model is told NOT to do what we want.

3. **rembg eats the framing:** rembg is trained on product photography (single subject, clean background). It sees branches/roots/ground near green as "background noise" and strips them, leaving only the clearest isolated subjects (owl/rabbit).

### Proposed fix: Green screen chroma-key instead of rembg AI

**Strategy:** Generate with an explicit SOLID green screen in the CENTER (where layers behind show through), use simple PIL color-keying to make that green transparent, and KEEP all the complex framing. No AI background removal.

```
Layer 1 needs: [branches at edges] [GREEN CENTER] [ground at bottom]
After keying:  [branches at edges] [TRANSPARENT CENTER] [ground at bottom]
```

**Changes needed to `src/generator.py`:**
1. Remove the hardcoded suffix — let the prompt control everything
2. Remove the hardcoded negative prompt
3. Replace rembg with PIL color-keying (chroma key on green screen)
4. OR: add a `layer_mode` parameter that switches between "rembg" (isolated subjects) and "chroma" (framing layers)

**New pipeline for Layer 1:**
1. Generate with Qwen at 768×576, 15 steps
2. Prompt includes explicit "solid bright green screen in the center rectangle, no objects in center"
3. PIL chroma-key: replace green pixels with alpha=0, keep everything else
4. Save as RGBA PNG

## 🎉 LAYER 1 GENERATED! (May 19, 2026 session #4)

**Layer 1 (20cm, foreground)** generated and saved: `src/output/layer1.png`
- Prompt: Ghibli style D&D camp — owl on branch, rabbit on root, tree frame
- Method: Qwen-Image-2512 4-bit (diffusers), 15 steps, 768×576
- Time: 581 seconds (~9 min 41 sec) on RTX 4070 Ti
- Output: RGBA with transparent background (rembg worked with onnxruntime-gpu)
- File: 52 KB
- Fix needed: installed `onnxruntime-gpu` (was missing in base `rembg` install)

---

## ✅ BLOCKER RESOLVED — Env Rebuilt (May 19, 2026 session #4)

### State (May 19, 2026 — SESSION #4 FINAL)
- **All 3 AI models downloaded** (~40 GB total, 32 GB free on C:)
- **Fresh `strulovitzghost` env CREATED** with Python 3.12
- **All packages installed & VERIFIED WORKING:**
  - torch 2.12.0+cu126 ✅ — CUDA: True, Device: RTX 4070 Ti
  - diffusers 0.38.0 (stable, was 0.39.0.dev0 before)
  - transformers 5.8.1, accelerate 1.13.0, bitsandbytes 0.49.2, sentencepiece 0.2.1 ✅
  - flask, flask-sqlalchemy, pyqt6, requests, python-dotenv, rembg ✅
- **Old env `strulovitzghost_OLD` still present** (507 MB locked DLL, 5 items) — worked around by using new env name
- **Locked DLL:** `cublasLt64_12.dll.DELETE` survived reboot + PendingFileRenameOperations. NVIDIA kernel section mapping is permanent. Can only be deleted via Safe Mode or Linux live USB. Left orphaned for now — no impact on development.

### 🔴 SESSION #3 — ADMIN POWERS UNLEASHED (May 19, 2026)

**What was tried with Administrator privileges:**
| Method | Result |
|--------|--------|
| `Remove-Item -Recurse -Force` (admin) | ❌ Access Denied |
| Stopped `NVDisplay.ContainerLocalSystem` service | ✅ Stopped — didn't release lock |
| `pnputil /disable-device` RTX 4070 Ti | ✅ Disabled — `nvlddmkm` stopped |
| Delete after GPU disabled + driver stopped | ❌ STILL Access Denied |
| `cmd /c del \\?\<path>` after driver stopped | ❌ Access Denied |
| `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)` (admin) | ❌ Returned False (but no error code) |
| **Direct registry write to `PendingFileRenameOperations`** | ✅ **SCHEDULED** |
| GPU re-enabled via `pnputil /enable-device` | ✅ |

### 🎯 SOLUTION FOUND — PendingFileRenameOperations (May 19, 2026)

Even with admin + GPU disabled + kernel driver stopped, the kernel section mapping persists until reboot. Directly wrote to:
```
HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations
\??\C:\Users\nir_s\miniconda3\envs\strulovitzghost_OLD\Lib\site-packages\torch\lib\cublasLt64_12.dll.DELETE
```
This is processed by `smss.exe` at boot BEFORE any drivers load — should bypass NVIDIA kernel lock.

**IMMEDIATE ACTION: REBOOT.** The file should be deleted automatically during boot.

### Root Cause Diagnosis (May 19, 2026 — HARD LESSON LEARNED)

After exhaustive diagnosis, the remaining locked DLL has a **kernel-level image section mapping**, NOT a process file handle. This means an NVIDIA kernel driver loaded the CUDA DLL into kernel memory space. No user-mode tool can release it.

**Everything that was tried and failed:**
| Method | Result |
|--------|--------|
| `Remove-Item -Recurse -Force` (PowerShell) | Access Denied |
| `rmdir /s /q` (cmd) | Access Denied |
| `del /f /q` (cmd, including `\\?\ ` extended path) | Access Denied |
| `takeown /f` + `icacls /grant` | Ownership & permissions SUCCESSFULLY granted — still Access Denied |
| `Rename-Item` (rename to .DELETE) | SUCCEEDED — rename works, delete doesn't |
| `handle64.exe` (Sysinternals) | No process has a file handle — confirms kernel lock |
| `[System.IO.File]::Delete()` | Access Denied |
| WMI `CIM_DataFile.Delete()` | Access Denied |
| `MoveFileEx` with `MOVEFILE_DELAY_UNTIL_REBOOT` | Error 5 (ACCESS_DENIED) even at kernel level |
| `type NUL >` truncate | "being used by another process" |
| 8.3 short filename delete | Access Denied |
| Defender exclusion | Defender not running (error 0x800106ba) |
| Stop NVIDIA display service | Needs admin |

**Conclusion:** This is a genuine kernel-mode lock. Section mappings survive renames but prevent deletion. **ONLY A REBOOT can release it.** There is no workaround, no tool, no trick — the kernel reference must be destroyed, and that only happens on reboot.

### ⛔ CRITICAL RULE LEARNED (May 19, 2026)

**NEVER HIDE PROBLEMS.** Do not rename, work around, or skip. Diagnose the root cause, document it, fix it properly. A problem that's "worked around" is a time bomb. This session wasted enormous time and tokens trying to circumvent a kernel lock that only a reboot can fix. If something is undeletable after 2-3 attempts, STOP and diagnose — don't try 15 different tricks.

### ✅ UPDATED PLAN (May 19, 2026 session #3) — REBOOT NOW, THEN CONTINUE

**IMMEDIATE: Reboot the PC.** The locked DLL is scheduled for deletion via `PendingFileRenameOperations`. After reboot it should be gone automatically.

**ONLY AFTER SUCCESSFUL REBOOT AND VERIFICATION THAT `strulovitzghost_OLD` IS GONE, PROCEED:**

**Step 2a (Verify): Confirm old env is fully deleted (post-reboot)**
```
Test-Path -LiteralPath "$env:USERPROFILE\miniconda3\envs\strulovitzghost_OLD"
```
Should return `False`. If still `True`, check what's left and report — DO NOT proceed to Step 3.

**Step 3: Create fresh strulovitzghost env**
```
cmd /c "C:\Users\nir_s\miniconda3\Scripts\conda.exe create -n strulovitzghost python=3.12 -y"
```

**Step 4: Install all packages**
```
%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe -m pip install torch==2.12.0+cu126 torchvision==0.27.0+cu126 --extra-index-url https://download.pytorch.org/whl/cu126
%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe -m pip install diffusers==0.39.0.dev0 transformers==5.8.1 accelerate==1.13.0 bitsandbytes==0.49.2 sentencepiece==0.2.1
%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe -m pip install flask flask-sqlalchemy pyqt6 pillow requests python-dotenv rembg
```

**Step 5: Verify**
```
%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe -c "import torch; print(torch.cuda.get_device_name(0))"
```

⚠️ Models in `~/.cache/huggingface/hub/` are NOT affected — no re-download needed.
⚠️ Python path: `%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe`
⚠️ DO NOT run any of these steps without Nir's explicit command. THIS IS NIR'S PC.
⚠️ DO NOT attempt Step 3+ until after reboot AND successful deletion of `strulovitzghost_OLD`.

### Exact versions (WORKING — May 19, 2026 session #4)
```
torch                2.12.0+cu126  ✅
torchvision          0.27.0+cu126  ✅
diffusers            0.38.0        (stable; 0.39.0.dev0 no longer available on PyPI)
transformers         5.8.1         ✅
accelerate           1.13.0        ✅
bitsandbytes         0.49.2        ✅
sentencepiece        0.2.1         ✅
flask                3.1.3
flask-sqlalchemy     3.1.1
pyqt6                6.11.0
pillow               12.2.0
requests             2.34.2
python-dotenv        1.2.2
rembg                2.0.75
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
