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

**Hardware:** RTX 4070 Ti 12GB — Qwen 4-bit generation works (~9 min per layer at 768×576 / 15 steps)

### 🎉 ALL 6 LAYERS GENERATED! (May 19, 2026)

Green screen pipeline: Qwen-Image-2512 (15 steps, 768×576) → chroma-key + despill.

| Layer | Content | File | Green keyed | Time |
|-------|---------|------|-------------|------|
| 1 🦉 | Owl, rabbit, tree branches (20cm) | `layer1.png` | 52% | 9.1m |
| 2 🧝‍♀️ | Elf paladin + Human druid (~3m) | `layer2.png` | 60% | 9.2m |
| 3 🔥 | Dwarf cleric + Halfling thief (~10m) | `layer3.png` | 41% | 9.3m |
| 4 🐉 | Tiefling fighter + Dragonborn (~20m) | `layer4.png` | 65% | 9.1m |
| 5 🌳 | Ancient magical oak forest | `layer5.png` | 37% | 9.0m |
| 6 🌙 | Night sky, moon, mountains | `layer6.png` | 42% | 9.1m |

**Total: ~54 min for 6 layers.** All RGBA in `src/output/`.

### 🔧 NIR'S CORRECTIONS — V2 PRINCIPLES (May 19, 2026)

From physical Pepper's Ghost testing with 6 semi-transparent plastic layers:

**1. NO BACKGROUNDS — ONLY OBJECTS.** No ground, mountains, fire behind characters. Backgrounds seen through closer layers destroy the illusion.

**2. EMPTY CENTER EVERY LAYER.** Transparent space in middle for layers behind. Objects at edges/top/bottom, never center.

**3. CHARACTERS MUST BE BRIGHT.** Semi-transparent plastic dims everything — characters must punch through.

**4. FAR APART → CLOSE TOGETHER with depth.** Layer 2 far apart (block everything behind), layer 3 closer, layer 4+ overlapping OK.

**5. SCALING: -15% per layer.** Layer 1=100%, 2=85%, 3=70%, 4=55%, 5=40%, 6=25%.

**6. VERTICAL STAGGERING — deeper = HIGHER.** Nir looks from above. Each deeper layer's content sits higher on canvas.

**7. NO FULL-HEIGHT OBJECTS.** Trees top-to-bottom seen through characters. Confine vertical objects to upper half or bottom third.

**8. NO GROUND.** Destroys illusion when seen through closer characters.

**9. PHYSICAL SETUP:** 6 layers, 3 monitors. Monitor #3 has polarization issues (layer 5 invisible). Nir looks from slightly above (crouched/bar stool). Only ~1 layer visible through previous one.

**10. PER-LAYER V2 SPEC:**
- **L1:** Rabbit + root at bottom. No owl, no branches. 100% scale. Bright.
- **L2:** Elf + Human girls on log, gossiping. Far apart. 85%. Bright. No ground.
- **L3:** Dwarf + Halfling arguing. No fire (or very dim). 70%. Closer.
- **L4:** Tiefling + Dragonborn SITTING on rocks. Together. 55%. No ground.
- **L5:** Few trees, upper half only, self-contained, not bright.
- **L6:** Moon + stars only. No mountains. 25%.

### ⛔ CRITICAL RULES (May 18, 2026 — updated May 19)

1. **NEVER download models without explicit permission.** HuggingFace `snapshot_download` filled 47 GB disk. Models are downloaded via GUI buttons only, never automatically by any script or test. Before any download, report size and ask.

2. **Conda env Python path:** `%USERPROFILE%\miniconda3\envs\strulovitzghost\python.exe` — always use this full path, never `conda run` (hangs in PowerShell).

3. **Any command that might write large amounts of data** (downloads, generations, cache writes) MUST be confirmed with user first.

4. **DO THE FULL JOB.** Never reward hack, never do a tiny part of what Nir asked, never ignore parts of the request, never do a half-ass job to save time. Complete everything asked.

5. **⛔ NEVER RUN SYSTEM-MODIFYING COMMANDS WITHOUT PERMISSION.** This is Nir's computer. Never create conda environments, install packages, delete files, create directories, or run ANY command that modifies the system without Nir's explicit permission. Ask first, explain what the command will do, and wait for approval. This rule was violated on May 19, 2026 (unauthorized conda create) — MUST NEVER HAPPEN AGAIN.

6. **🗣️ TALK BEFORE ACTING — ALWAYS.** Before ANY command or action, discuss with Nir first. Never surprise-execute. This includes git commands, file writes, directory creation, anything. Explain what you're about to do and get approval.

7. **⚖️ OFFER OPTIONS WITH PROS/CONS.** When there are multiple approaches, present them as choices with tradeoffs. Let Nir decide the path.

8. **⏱️ TIME ESTIMATES FOR EVERY MICRO-STEP.** Before any action, tell Nir exactly how long each sub-step will take. Set short timeouts on all commands (5-10 sec for checks, 30-60 sec for generation, max 120 sec). Never let a command hang indefinitely — if it times out, report and discuss next steps with Nir.

9. ~~**🚫 NEVER USE rembg.**~~ **REVOKED May 19.** The "rembg destroyed Layer 1" diagnosis was wrong. The real cause was the generator's hardcoded suffix ("isolated subject, small and centered") + negative prompt ("busy background, multiple objects") which contradicted our prompt. rembg just received already-broken output. The tool wasn't the problem — the prompt was.

10. **💾 SAVE EVERYTHING TO GITHUB FOREVER.** Every correction, direction, decision, or instruction Nir gives — save to MEMORY.md immediately, commit, and push. Permanent rule for all sessions. No exceptions. "Immediately" means immediately.

---

## 🎯 FINAL CLEANEST PIPELINE (May 19, 2026)

Three tools, each doing what it's best at. One model in GPU at a time.

### Step 1 — Qwen-Image-2512: DRAW
Generate layer on flat #00FF00 green screen.
- REMOVE hardcoded suffix ("isolated subject, small and centered") from generator
- REMOVE contradictory negative prompt ("busy background, multiple objects, frame filling")
- APPEND green screen formula: "Completely solid, uniform flat chroma key green color, hex #00FF00. No shadows, no gradients, no textures, no highlights. Even illumination across a perfectly flat green surface."
- Negative: "shadows on background, gradient background, studio lights, green screen stand, wrinkles, fabric texture, environment, wall texture, vignette, color bleeding, light spill, rim light"
- Unload generator when done

### Step 2 — Qwen-Image-Edit-2509: CLEAN
Clean green spill from subject edges.
- Prompt: "Remove any green color bleeding from the edges of the subjects. Clean up the green background so it is perfectly uniform #00FF00. Do not modify any subjects in any way — keep all details, textures, animals, branches, and ground completely unchanged."
- Unload edit model when done

### Step 3 — PIL + despill: KEY
Convert #00FF00 to alpha=0. Apply despill algorithm to clean remaining green tint.

---

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
| `unsloth/Qwen-Image-2512-GGUF` | ~13 GB | ✅ Downloaded — only for ComfyUI path |
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

### Open questions for Google AI search — ANSWERS

### Answer #2: Negative prompts to prevent background artifacts on green screen

**CRITICAL:** CFG must be above 1.0 (ideally 3.5-7.0) or Qwen-Image-2512 IGNORES the negative prompt entirely.

**Three categories of negative prompts:**

1. Core Background Exclusion (natural language):
```
background scenery, studio equipment, lighting stands, softboxes, props,
floor visible, walls, shadows on the background, gradients,
photographic studio context, complex environment, outdoor setting,
interior design elements
```

2. Artifact & Cleanliness Guard:
```
blurry background, bokeh, out of focus elements, depth of field artifacts,
watermark, text overlay, signature, vignette, borders, frames,
digital compression noise
```

3. Green Color Bleed Prevention (CHROMA KEY CRITICAL):
```
green tint on skin, green color bleeding, color fringing,
chromatic aberration, green light reflections on subject,
translucent edges, green spill
```

**Complete combo string (under 12 concepts — don't dilute):**
```
background scenery, studio equipment, floor, wall, shadows on background,
bokeh, blurry background, watermark, green color bleed, color fringing,
green reflections on skin
```

**Critical synergy:** Positive prompt MUST embed strict structural anchors.
- BAD: "A realistic photo of a chef on a green screen." (model draws kitchen with green screen hanging somewhere)
- GOOD: "Completely flat, uniform, solid chroma key green screen background (#00FF00). Smooth background with no shadows, no gradients, no depth. Solid monochrome color background."

### Answer #5: Complete Qwen-Image-2512 + Edit-2509 pipeline for transparent PNGs

**CRITICAL WARNING:** Never ask Qwen-Image-Edit for "transparent background" — it renders a literal gray-and-white checkerboard pattern instead of true alpha. This is a documented failure mode.

**The production ComfyUI pipeline (3 steps):**

```
Step 1: Qwen-Image-2512  →  Generate base image (don't ask for transparency here)
Step 2: Qwen-Image-Edit-2509  →  "Replace background with solid #00FF00, isolate the subject"
Step 3: Color to Mask node  →  Convert green pixels to alpha → Save as transparent PNG
```

**Step 2 isolation prompt (confirmed working):**
```
Isolate the main subject. Replace everything else in the background with a completely solid,
uniform neon green color (#00FF00) with no shadows or gradients.
```

**Step 3 settings:**
- Color to Mask node targeting exact green hex
- Color tolerance: 0.01 to 0.05
- Output: PNG with alpha channel

**For our Python/diffusers pipeline (not ComfyUI):**

Option A (simpler): Qwen-Image-2512 with green screen prompt → PIL chroma-key green to alpha. Skip the Edit model entirely.

Option B (cleaner edges): Qwen-Image-2512 → Qwen-Image-Edit to clean up green spill on edges → PIL chroma-key. Use only if Option A shows color bleeding on hair/edges.

**VRAM management for local 12GB GPU:**
- Load generation model → generate → del + empty_cache()
- Load edit model → edit → del + empty_cache()
- Never both models in memory simultaneously

### Answer #4: Qwen-Image-Edit-2509 background removal prompts that actually work

**Key fact:** Qwen-Image-Edit-2509 also cannot output transparency directly (RGB only, like the generator). The technique is: replace background with a SOLID color → then chroma-key that color in post-processing.

**Confirmed prompt examples:**

For portraits/people:
```
Extract the person from the image. Replace the background with a solid black color
while keeping the person's face, features, body proportions, and lighting completely unchanged.
```

For products/objects:
```
Isolate the main product. Replace the cluttered background with a clean, solid white
studio backdrop while keeping the product positioning, textures, and lighting unchanged.
```

Chroma key green screen method:
```
Remove the background and replace it with a solid, uniform green screen color,
preserving only the subject exactly as it appears.
```

**Why these work — 3 required constraints:**
1. Explicit color definition — never say "remove background", say "replace with solid black/white/green"
2. Fidelity constraints — "keeping the subject completely unchanged" prevents facial/body distortion
3. Lighting holds — "maintaining original lighting and color palette" prevents shadow/highlight changes

**Best workflow:** Use inpainting masks if available (ComfyUI). Otherwise: Edit → key the solid color.

**Pipeline insight:** Since Qwen-Image-2512 already generates with green screen, we may not even need the Edit model. Green → PIL chroma-key directly might work. The Edit model would only help if the generator leaves green spill on edges/hair.

### Answer #3: Does Qwen-Image-2512 output alpha/transparency directly?

**NO.** Qwen-Image-2512 outputs flat RGB only. No alpha channel.

Google AI claims Qwen-Image-Layered can take a text prompt and generate RGBA layers directly — but this contradicts the HuggingFace docs which show image-only input (decomposition). This needs verification.

**Practical conclusion:** Our pipeline MUST be 2-step:
1. Qwen-Image-2512 → RGB with green screen background
2. Post-processing → RGBA with transparency (chroma-key or Qwen-Image-Edit)

No single-step transparent generation available from Qwen ecosystem (unconfirmed for Layered).

### Answer #1: How to prompt Qwen-Image-2512 for chroma key green background

**Working formula (from Google AI, confirmed):**

Positive prompt structure:
```
[Your Subject], centered, professional studio portrait photography.
The entire background is a single, completely solid, uniform flat chroma key green color, hex #00FF00.
The green background has no shadows, no gradients, no textures, and no highlights.
Even illumination across a perfectly flat green surface.
```

Negative prompt:
```
shadows on background, gradient background, studio lights, green screen stand,
wrinkles, fabric texture, environment, wall texture, vignette,
color bleeding, light spill, rim light
```

**Why this works:**
1. Never say "green screen" alone — model draws physical studio equipment (fabric, stands, lights)
2. "uniform flat chroma key green color, hex #00FF00" shifts attention to graphic element, not physical object
3. "no gradients, no highlights" + negative "rim light, light spill" prevents green light bouncing onto subject
4. hex #00FF00 gives unambiguous anchor for pure green — avoids model's tendency toward natural green gradients

**Recommended settings:**
- CFG Scale: 3.5 to 4.5 (slightly higher forces stricter background compliance)
- Output: PNG ONLY (JPEG artifacts ruin chroma key edges)

### Open questions for Google AI search

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
- **All 2 AI models downloaded** (~26 GB total)
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

---

## 📋 Appendix: Google AI Search — Verbatim Answers (May 19, 2026)

### Query #1: How to prompt Qwen-Image-2512 to generate images with pure chroma key green background that can be keyed out for transparency. What prompt wording actually works.

> To successfully generate images with a pure chroma key green background using Qwen-Image-2512, you must leverage its advanced Multimodal Diffusion Transformer (MMDiT) architecture, which responds best to hyper-specific, literal, and non-overlapping background descriptions. Buzzwords like "chroma key" alone often cause the model to generate actual studio equipment (like physical green cloth wrinkles or light stands).
>
> Instead, you need to enforce a digitally flat, uniform solid color and explicitly suppress environmental lighting shadows and reflections in your parameters.
>
> 🟩 The Working Prompt Formula
>
> Combine a precise subject description with a literal definition of the background hex color (#00FF00) and texture:
>
> Positive Prompt:
> `[Your Subject], centered, professional studio portrait photography. The entire background is a single, completely solid, uniform flat chroma key green color, hex #00FF00. The green background has no shadows, no gradients, no textures, and no highlights. Even illumination across a perfectly flat green surface.`
>
> Negative Prompt:
> `shadows on background, gradient background, studio lights, green screen stand, wrinkles, fabric texture, environment, wall texture, vignette, color bleeding, light spill, rim light`
>
> 🛠️ Why This Specific Structure Works in Qwen-Image-2512
>
> 1. Avoids the "Studio Prop" Trap — Because Qwen-Image-2512 understands semantic relationships deeply, writing "on a green screen" forces it to draw what it thinks a green screen studio looks like (fabric seams, stands, and lighting drops). Describing it as a "uniform flat chroma key green color, hex #00FF00" shifts its attention to a graphic element rather than a physical object.
>
> 2. Controls Light Spill and Rim Lighting — By default, the model tries to integrate subjects realistically with their environments. If you generate a person, it will try to bounce green light onto their hair or skin (light spill). The phrase "no gradients, no highlights" in the positive prompt, paired with "rim light, light spill" in the negative prompt, forces the model to clip the subject cleanly away from the flat backcloth.
>
> 3. Keeps It Flat — The inclusion of "hex #00FF00" gives the underlying text encoder a clear, unambiguous anchor for pure, high-saturation digital green, preventing the model from rendering natural "rich gradations of greens" that it usually prefers for landscapes.
>
> 🎛️ Recommended Generation Settings
>
> For the cleanest edges that key out seamlessly in post-production, use these settings in your API or ComfyUI pipeline:
>
> CFG Scale / Guidance Scale: Set to 3.5 to 4.5. Pushing the guidance slightly higher forces stricter compliance with the text prompt, ensuring the background doesn't wander into creative styling.
>
> Output Format: Always select PNG. Formats like JPEG introduce compression artifacts along the high-contrast borders between your subject and the green backdrop, which ruins a clean key.

### Query #2: What negative prompts work best with Qwen-Image-2512 to prevent unwanted background elements and artifacts when generating subjects on a solid green screen background.

> To achieve a clean, isolated subject on a solid green screen using Qwen-Image-2512, your negative prompt needs to address three core issues: background complexity, color bleeding, and texture artifacts. Because Qwen-Image-2512 responds best to a mix of natural language definitions and structural constraints rather than long, generic keyword lists, target the negative prompt strategically.
>
> Ensure your generation setup has Classifier-Free Guidance (CFG) set above 1.0 (ideally between 3.5 and 7.0), otherwise Qwen-Image-2512 will ignore the negative prompt entirely.
>
> Optimized Negative Prompt Strings
>
> 1. Core Background Exclusion (Natural Language Format)
> Qwen-Image models lean heavily on natural language understanding. Instead of just typing scenery, directly describe what shouldn't exist behind the subject:
> `"background scenery, studio equipment, lighting stands, softboxes, props, floor visible, walls, shadows on the background, gradients, photographic studio context, complex environment, outdoor setting, interior design elements."`
>
> 2. Artifact and Cleanliness Guard
> To stop the model from trying to ground the subject or adding standard rendering noise, explicitly ban text, composition lines, and common AI artifacts:
> `"blurry background, bokeh, out of focus elements, depth of field artifacts, watermark, text overlay, signature, vignette, borders, frames, digital compression noise."`
>
> 3. Preventing Green Color Bleed (Chroma Key Artifacts)
> When generating against a solid color, AI models frequently blend the background color into the subject's edges, hair strands, or skin tones. Stop color contamination with:
> `"green tint on skin, green color bleeding, color fringing, chromatic aberration, green light reflections on subject, translucent edges, green spill."`
>
> The Complete Combo String
> Combine these into a single, punchy list of under 12 distinct concepts to avoid diluting the model's focus:
> `background scenery, studio equipment, floor, wall, shadows on background, bokeh, blurry background, watermark, green color bleed, color fringing, green reflections on skin`
>
> Critical Positive Prompt Synergy
> Negative prompts do not work in isolation; they only subtract from what the positive prompt establishes. Qwen-Image-2512 tends to hallucinate environments if the positive prompt is too simple.
>
> To lock down a flat green screen background, always embed strict structural anchors in your positive prompt:
> Bad Positive: "A realistic photo of a professional chef on a green screen." (Qwen will likely render a kitchen with a green screen hanging up somewhere in the shot).
> Good Positive: "A crisp, clean studio photograph of a professional chef. The subject is perfectly centered. Completely flat, uniform, solid chroma key green screen background (#00FF00). Smooth background with no shadows, no gradients, and no depth. Solid monochrome color background."

### Query #3: Does Qwen-Image-2512 or any Qwen image generation model support outputting images with alpha channel or transparent background directly, without post-processing.

> Yes, Alibaba has an official Qwen model that directly outputs transparent images with an alpha channel. While the standard base text-to-image model Qwen-Image-2512 outputs flat RGB images, Alibaba specifically developed and open-sourced Qwen-Image-Layered.
>
> Qwen-Image-Layered
> Instead of generating a single flat rasterized image, Qwen-Image-Layered generates natively structured, editable RGBA layers.
> Native Transparency: It yields physically isolated elements directly in an RGBA format (Red, Green, Blue, Alpha).
> No Post-Processing Required: It does not use background-removal masks or green-screen filters as an afterthought. The model treats transparency natively as part of its generative output.
> How it works: It can take a text prompt or decompose a static flat image into isolated, transparent layers (e.g., separating a foreground subject cleanly from its background).
>
> Qwen-Image-2512 (Standard Base Model)
> The standard Qwen-Image-2512 text-to-image model is built for photorealism, fine text rendering, and landscapes. It handles pixel color generation but cannot natively create transparent backgrounds on its own. To get a transparent PNG from Qwen-Image-2512, you must route its output through post-processing nodes (like LayerDiffuse or a separate background removal step) within tools like ComfyUI.

### Query #4: Qwen-Image-Edit-2509 background removal prompt examples that actually work. How to tell it to remove the background and keep only the subject. Specific prompt wording that people have tested and confirmed.

> To remove a background and isolate a subject using Qwen-Image-Edit-2509, you must instruct the generative model to paint a uniform, solid background. Because it is a diffusion-based generative model and cannot natively output alpha-channel transparency (.png holes), testing shows that forcing a single solid color provides the best separation for clean post-processing.
>
> Confirmed Prompt Examples
>
> To get the best results, use these exact, community-tested prompt structures depending on your subject:
>
> For Portraits & People:
> `"Extract the person from the image. Replace the background with a solid black color while keeping the person's face, features, body proportions, and lighting completely unchanged."`
>
> For Products & Objects:
> `"Isolate the main product. Replace the cluttered background with a clean, solid white studio backdrop while keeping the product positioning, textures, and lighting unchanged."`
>
> The "Chroma Key" Green Screen Method:
> `"Remove the background and replace it with a solid, uniform green screen color, preserving only the subject exactly as it appears."`
>
> Why These Prompts Work: The Key Elements
>
> If you want to write your own prompts, you must include specific constraints to prevent Qwen from hallucinating or distorting your subject:
> 1. Explicit Color Definition: Do not just say "remove background". Tell it to replace it with "solid black", "solid white", or "a uniform green screen". This stops the model from painting a different creative scene.
> 2. Fidelity Constraints: Always append text like "keeping the subject completely unchanged" or "preserve pixel-perfect fidelity to original features." Without this, Qwen-Image-Edit-2509 can alter facial expressions, body weights, or product labels.
> 3. Lighting & Palette Holds: Include phrases such as "maintaining the original lighting and color palette." This prevents the model from changing the shadows or highlights on your subject to match the new background color.
>
> Pro-Tips for the Best Workflow
> Use Inpainting Masks if Possible: If you are using Qwen-Image-Edit-2509 in ComfyUI or a Web UI, paint a mask over the background. Masking combined with the text prompt ensures 100% of your subject remains untouched.
> The Post-Processing Step: Once Qwen outputs the image with your solid green, black, or white backdrop, pass it through a quick traditional node or tool (like Photoshop's Select Subject or ComfyUI's RMBG / BiRefNet nodes) to instantly key out the solid color and achieve true transparency.

### Query #5: Best workflow combining Qwen-Image-2512 + Qwen-Image-Edit-2509 for transparent PNGs

> To successfully generate images with Qwen-Image-2512 and isolate subjects using Qwen-Image-Edit-2509, you must account for a well-documented LLM quirk: Qwen-Image-Edit-2509 tends to interpret the phrase "transparent background" by rendering a literal, flattened gray-and-white checkerboard pattern rather than true alpha transparency.
>
> The most efficient, automated, and community-proven workflow links these two models inside ComfyUI, using a chroma-keying strategy combined with a secondary masking node to output flawless, transparent .png files.
>
> The ComfyUI Production Pipeline
> ```
> [ Step 1: Generation ]       [ Step 2: Solid Fill ]        [ Step 3: Matte & Output ]
>  Qwen-Image-2512       -->   Qwen-Image-Edit-2509    -->   Convert Mask to Alpha
> (Generate Base Image)       (Green Screen / Flat Back)     (Export Transparent PNG)
> ```
>
> Step 1: Base Image Generation (Qwen-Image-2512)
> Generate your high-fidelity asset using the standard text-to-image pipeline.
> Load Models: Add your qwen_2.5_vl_7b_fp8_scaled.safetensors text encoder and the primary diffusion model.
> K-Sampler Setup: For optimal realism and crisp edge definition, use 50 steps. If iterating rapidly or dealing with VRAM constraints, you can swap in the Qwen-Image-Lightning-4steps-V1.0.safetensors LoRA at 4 steps.
> Prompting: Clearly define your subject. Avoid asking for transparency in this first step; give the model a simple, unified background to make isolation cleaner later (e.g., "A detailed studio shot of a ceramic coffee mug, sitting on a plain studio table").
>
> Step 2: The "Chroma Key" Hack (Qwen-Image-Edit-2509)
> Instead of prompting Qwen-Image-Edit-2509 for a "transparent background" (which triggers the checkerboard failure), you will turn it into a virtual green-screen engine.
> Node Connection: Route the IMAGE output from your Step 1 VAE Decode directly into the image1 input of the TextEncodeQwenImageEditPlus node.
> Skip Resizers: Let the native Qwen node manage scaling. Bypassing standard scaling nodes prevents the alignment and blurriness bugs common to this model combination.
> The Prompt: Feed a highly descriptive isolation instruction to the text encoder:
> `"Isolate the main subject. Replace everything else in the background with a completely solid, uniform neon green color (#00FF00) with no shadows or gradients."`
> Execution: Run your K-Sampler. Qwen-Image-Edit-2509 will effortlessly track the semantic boundaries of your subject and cleanly repaint the background into a flat chroma key color.
>
> Step 3: Generating Alpha Channel and Saving PNG
> Because the image output is still an RGB file containing flat neon green pixels, you need a quick node-based filter to strip it out and convert it into a true alpha transparency layer.
> Masking Node: Pass the output image into a Mask to Region or a Color to Mask node.
> Target Color: Sample or input the exact hexadecimal/RGB value of your solid background (e.g., Neon Green). Adjust the color tolerance slider slightly (usually around 0.01 to 0.05) to cleanly capture the edges without bleeding into your subject.
> Invert & Join: Invert the mask so that the subject is selected, then pipe it into an Image to Mask (Alpha) or Join Image with Alpha node.
> Save File: Connect the combined image to a standard Save Image node. Ensure your output extension is set explicitly to .png to preserve the newly embedded transparency channel.
>
> Summary Checklist for Local Deployment
> | Pipeline Element | Recommended Model / Configuration | VRAM Optimization |
> |------------------|-----------------------------------|-------------------|
> | Generator | Qwen-Image-2512 (BF16 or FP8) | 4-Step Lightning LoRA |
> | Editor | Qwen-Image-Edit-2509 (FP8 or GGUF) | Use EmptySD3LatentImage node |
> | Isolation Prompt | "Replace background with solid color #00FF00" | Avoid the word "transparent" |
> | Output Format | Clean RGB + Chroma Mask | Export via transparent .png node |

### Query #6: Using rembg on AI-generated images with green screen background — better or worse?

> rembg performs worse on flat chroma key green (#00FF00) backgrounds than it does on natural, contextual environments.
>
> Because rembg relies on deep learning Salient Object Detection (SOD) models (like u2net or birefnet), it uses environmental context, shadows, and semantic meaning to identify the subject. It was not trained on chroma key images. When presented with a perfectly flat, neon green #00FF00 void, the AI loses spatial cues, frequently resulting in jagged edges, "eaten" subjects, or leftover green halos.
>
> If you are generating AI images specifically to remove the background later, stop generating them with green screens. Generate them with a natural background or a neutral, textured studio backdrop instead. However, if you already have green screen AI generations, you can apply specific settings and preprocessing techniques to optimize your rembg results.
>
> 1. Switch to a Optimized Model (birefnet or isnet)
> The default model (u2net) struggled heavily with flat tones. Modern versions of rembg support highly superior models.
> `birefnet-general` or `isnet-general`: These models feature significantly higher edge accuracy and resolve fine details (like hair) far better against flat backdrops.
>
> Python Example:
> ```python
> from rembg import remove, new_session
> # Explicitly call a high-fidelity model
> session = new_session("birefnet-general")
> output = remove(input_image, session=session)
> ```
>
> 2. Preprocessing: The "Fake Natural" Trick
> Since rembg looks for depth and context, you can drastically improve its accuracy by programmatically replacing the flat #00FF00 green screen with a detailed, high-contrast texture (like a brick wall, gravel, or a gray gradient studio backdrop) before passing it to rembg.
> Use a standard color-threshold (chroma-key) script via OpenCV to find the exact #00FF00 pixels.
> Replace those green pixels with a detailed stock background image.
> Feed this newly merged image into rembg. Because the AI can now perceive "depth" and a realistic background/foreground separation, it will generate a much cleaner cutout.
>
> 3. Post-Processing: Post-Alpha Despilling
> AI-generated green screens often cause "green spill," where neon green light reflects unnaturally onto the edges of the subject's hair, clothes, and skin. rembg will not remove this color distortion; it will just cut the subject out, leaving them with a sickly green glow.
>
> To fix this in your Python pipeline, isolate the alpha channel generated by rembg and apply a despill algorithm to the RGB channels:
> ```python
> import cv2
> import numpy as np
> # Load the image after rembg processed it (must have alpha channel)
> img = cv2.imread("output.png", cv2.IMREAD_UNCHANGED)
> b, g, r, a = cv2.split(img)
> # Classic digital despill algorithm: limit green to the average of red and blue
> g_despilled = np.minimum(g, (r.astype(np.uint16) + b.astype(np.uint16)) // 2).astype(np.uint8)
> # Recombine channels
> despilled_img = cv2.merge([b, g_despilled, r, a])
> cv2.imwrite("final_clean_output.png", despilled_img)
> ```
>
> 4. Use Built-in Alpha Matting Arguments
> If you are running rembg from the command line, use the built-in alpha matting feature. This tells the algorithm to perform a dedicated foreground/background gradient erosion step around the edges to clean up loose pixels.
> Use the following flags in your CLI:
> `rembg i input.png output.png -a -ae 15`
> -a: Activates alpha matting.
> -ae 15: Sets the erosion size. Increase or decrease this value depending on how much green fringe is leaking into the edges of your subject.

---

## 📋 Appendix B: Google AI Search — Spatial Composition (May 19, 2026)

### Query #7: How to control exact subject position and size in Qwen-Image-2512 prompts

> To control exact subject size and position in Qwen-Image-2512 prompts, use highly specific camera angles (e.g., "low-angle shot," "bird's eye"), spatial anchors (e.g., "anchored to the bottom edge," "resting on the bottom floor"), and aspect ratio modifications (e.g., landscape 16:9).
>
> Because text-only prompting can be imprecise with exact percentages, spatial composition uses relative terms.
>
> Best Prompting Keywords for Bottom Placement (15-20% Scale)
>
> Camera Angle: "Ultra-wide angle shot," "ground-level view," "looking up from below," or "elevated high-angle shot looking down".
>
> Spatial Anchors: "Occupying only the bottom 20% of the frame," "anchored to the bottom edge," "submerged at the bottom," or "resting on the bottom border".
>
> Framing Descriptors: "Wide shot," "far away shot," or "small scale" (prevents the model from creating a macro close-up).
>
> Negative Prompts: "Close-up," "macro," "zoomed in," "filling the entire frame," "centered".
>
> Example Prompt Templates
>
> Example 1: A small, low-lying object (e.g., a tiny boat on water)
> "A wide, extreme long shot of a small wooden boat resting on the water. The boat occupies only the bottom 15% of the frame, leaving the upper 85% of the frame to a vast, moody sky and a wide horizon. Cinematic lighting, photorealistic, wide panoramic view."
>
> Example 2: A small character (e.g., a tiny cat at the bottom)
> "A high-angle, ultra-wide environmental shot. A tiny fluffy cat sitting on the bottom border, looking up at a massive, empty room. The cat occupies a small scale, taking up only 20% of the vertical height. Natural soft morning light, hyper-realistic, highly detailed."
>
> 2 Essential Tips for Perfect Execution
> Use the Right Aspect Ratio: The base model works well when the aspect ratio matches the composition. For an expansive, empty upper section, use a horizontal layout like 16:9 (1664×928) or 4:3 (1472×1104).
> Turn off Prompt Expansion: If you are using a frontend API/UI (like Fal.ai) that auto-expands prompts, toggle it off. Expansion will likely add "beautiful detailed subject" and override your 15-20% scale instruction.

### Query #8: How to force negative space and make subject small at a specific edge

> To force negative space and keep your subject small and cornered in Qwen-Image-2512, you must explicitly define the background as the dominant subject and anchor the real subject using literal spatial dimensions. Because Qwen uses a Multimodal Diffusion Transformer (MMDiT), mentioning an object naturally prompts it to fill the canvas unless the surrounding canvas is heavily described.
>
> Use these targeted strategy steps to overrule the model's auto-zooming behavior:
>
> 1. Reverse the Prompt Hierarchy
> Qwen weighs concepts based on their position and word count in the prompt. If you start with your subject, it becomes the primary focus. Instead, start with the negative space as if it were the main subject.
> ❌ Bad (Subject first): "A small lone sailboat at the bottom of the frame, surrounded by an immense empty blue ocean." (The model sees "sailboat" first and zooms in).
> ✅ Good (Background first): "A vast, massive expanse of an empty, minimalist deep blue ocean filling 90% of the frame. In the extreme bottom edge, a tiny, microscopic sailboat is positioned, occupying less than 5% of the total canvas space."
>
> 2. Use Absolute and Percentage Language
> Vague terms like "at the bottom" or "isolated" fail because the model still defaults to a centered composition. Force spatial constraint by using percentages, framing descriptions, and exact layout terminology:
> Specify scale: Use words like "microscopic scale," "tiny silhouette," "distant speck," "extreme wide shot," or "minuscule size."
> Define canvas distribution: State exactly how much of the canvas is empty (e.g., "The top 85% of the image is completely blank white space").
> Edge positioning: Use exact anchor phrases: "hugging the absolute bottom edge," "nestled in the far bottom-right corner," or "positioned at the lowest margin."
>
> 3. Turn Off the Prompt Enhancer
> If you are generating via an interface or API that uses an automatic "Prompt Enhancer" or "Rewriter," turn it off. The Qwen-Image-2512 prompt helper is great for mood boards but terrible for precise layouts. It will automatically inject descriptive flourishes, textures, and extra details onto your subject, which inadvertently tells the model to scale up the subject to show those details. Keep your prompt completely literal.
>
> 4. Treat Negative Space as a Concrete Object
> Instead of leaving the background empty, name it as a solid, overwhelming element so the model has something explicit to generate instead of your subject.
> For a studio background: "A seamless, completely blank, solid matte grey concrete wall dominates the entire frame..."
> For nature background: "An endless, clear, completely cloudless stark white sky occupies almost the entire image..."
>
> 5. Structure Your Negative Prompt Logically
> Qwen-Image-2512 responds best to a natural language, NLP-style negative prompt rather than a wall of comma-separated keyword tags. Explicitly ban the zooming behavior in your negative prompt box:
> Negative Prompt: "close-up shot, medium shot, zoomed-in view, subject filling the frame, centered composition, cropped subject."

### Query #9: Qwen-Image prompt techniques for framing and negative space

> To create large areas of empty or negative space around your subject in Qwen-Image (or similar vision-language models), you need to use explicit aspect ratios, minimalist keywords, and precise framing directives.
>
> 1. Aspect Ratio Control
> Use wide or tall ratios: Specify aspect ratios like --ar 16:9 (horizontal canvas) or --ar 9:16 (vertical canvas).
> Isolate the subject: Extreme ratios naturally create more room away from the center.
>
> 2. Precise Composition Terms
> Negative space: Use the exact phrase "large areas of negative space."
> Minimalist composition: Use "minimalist composition" or "clean, uncluttered background."
> Rule of thirds: Specify "subject placed in the lower third" or "subject off-center in the bottom right corner."
> Scale contrast: Use "tiny subject in a vast landscape" or "microscopic scale" to force the model to shrink the subject.
>
> 3. Background Simplification
> Uniform surfaces: Describe the empty area specifically, such as "solid matte background," "foggy void," "clear endless sky," or "studio backdrop."
> Avoid detail bleed: Do not describe textures or secondary objects, as the model will try to fill the empty space with them.
>
> 4. Framing Directives
> Extreme Long Shot (ELS): Forces the camera far back, making the environment dominant.
> Bird's-eye view: Creates a large floor or ground plane around the subject.
> Low-angle shot: Looking up at a subject creates massive negative space using the sky.
>
> 5. Example Prompt Formulas
> Vertical Negative Space (Sky/Void):
> "An extreme long shot of a lone traveler standing at the very bottom edge of the frame. The upper 80% of the image is a vast, empty, solid grey misty sky. Minimalist composition, deep negative space above the subject, 9:16 aspect ratio."
> Horizontal Negative Space (Studio/Clean):
> "A single ceramic vase placed in the far bottom-right corner. The entire left and upper sections of the image are a completely empty, flat beige wall. Studio lighting, heavy negative space, clean minimalist aesthetic, 16:9 aspect ratio."
> Natural Environment Space:
> "A tiny silhouette of a person sitting on a bench, positioned in the lower-left grid intersection. Surrounded by an immense, unbroken field of white snow filling the rest of the frame. High contrast, minimalist photography, immense negative space."

---

## 📋 REMAINING TODO (May 19, 2026 — end of session)

| # | Task | Status |
|---|------|--------|
| 1 | Update README — says "Planning Phase" but V2 pipeline complete | ✅ DONE |
| 2 | Image preview in GUI — user can't see generated result in-app | ✅ DONE |
| 3 | Update tests for V2 pipeline (test_api.py, test_e2e_real.py) | ✅ DONE |
| 4 | ~~Remove Qwen-Image-Edit~~ | ✅ DONE |
| 5 | ComfyUI path — exists in code but never tested end-to-end | ⬜ TODO |
| 6 | Hierarchical architecture (classroom→school→county scaling) | ⬜ TODO |
| 7 | Update setup.bat for V2 dependencies | ✅ DONE |
| 8 | 3-color chroma-key feature in GUI (red/green/blue selector) | ✅ DONE |
| 9 | combine.py for hierarchical layer stacking | ✅ DONE |
| 10 | LLM splitter updated with V2 principles | ✅ DONE |
| 11 | Generator V2 prompts (green screen + spatial composition) | ✅ DONE |

---

## 🆕 NEW TODO (May 20, 2026 session)

| # | Task | Status |
|---|------|--------|
| 12 | Fix progress bar stuck at 10% — ProgressTracker step counting bug in generator.py | ⬜ TODO |
| 13 | Fix LLM template castrating GPT 5.5 text — TYPE A extraction shrinks prompts from ~600 chars to ~125 | ⬜ TODO |
| 14 | Fix Worker negative prompt field disappearing after first layer generation | ⬜ TODO |

### 🔴 BUG DISCOVERED — LLM template destroys GPT 5.5 prompt quality (May 20)

**Root cause:** The LLM template instructs qwen3:14b to "Remove any meta-instructions like 'Important:', 'Transparent PNG layer.', 'Prompt to copy/paste:', 'Draw only...' — but this causes the LLM to aggressively strip actual art direction content, not just headers.

**Evidence:** GPT 5.5 Layer 2 prompt (~600 chars with detailed pose, clothing, staff description) was reduced to 125 chars by qwen3:14b. Character lost position ("on the left"), orientation ("back towards us"), clothing details ("magenta burgundy purple robes with gold trim, cape-like back"), and staff description.

**Required fix:** Change TYPE A instruction from "extract/remove" to "preserve verbatim." Add explicit: "DO NOT summarize, shorten, or rewrite — pass through the exact prompt text. Only remove the literal label headers like 'Prompt to copy/paste:' and 'Negative prompt:' — keep ALL the descriptive content between headers intact."

### 🔴 BUG — Worker negative prompt field invisible on 2nd+ layers

Negative prompt is generated by LLM and stored in DB (confirmed for Q#4), but when worker claims subsequent tasks, the negative prompt field (red label + QTextEdit) doesn't appear. The `setVisible(True)` call may be missing in the claim flow for subsequent claims after a generation cycle.

### 🔴 BUG — Progress bar perpetually at 10%

Known since earlier session. The ProgressTracker in generator.py never fires progress updates during diffusion steps because the step_times list never receives its first entry. Bar stays at 10% until chroma-key at 92%.
