# 🧪 LAN Test #02 — ITG Distributed on 2 Machines (GUI Test)

**Date:** May 25, 2026 | **Status:** ⏳ READY TO EXECUTE | **Mode:** ITG (Image To Ghost) | **Author:** Laptop AI

---

## 🤖 AI AGENTS — START HERE ON RESTART

### ⛔ CRITICAL: This is an EXPERIMENT, not a black box. Nir must SEE the system working.

**Nir's observation dashboard — open ALL of these on the Laptop:**

| Window | What | Why |
|--------|------|-----|
| **Browser** → `http://localhost:5000` | Website dashboard | Watch questions appear, tasks grow, layers complete |
| **GUI #1 (Boss ITG)** | Boss state machine | Watch state changes: scanning → processing → waiting → combining → done |
| **GUI #2 (Worker ITG)** | Worker progress | Watch progress bars, image previews, task claims |
| **ComfyUI terminal** | Black PowerShell window | Shows real AI generation: "generating... (15s)", "generating... (32s)" |

**On the Desktop, Nir must also watch:**
| Window | What | Why |
|--------|------|------|
| **GUI #1 (Worker ITG)** | Desktop Worker | Watch it claim tasks and split via Laptop's ComfyUI over LAN |
| **GUI #2 (Client ITG)** | Desktop Client | Upload image + watch auto-refresh + download final layers |

**The experiment is NOT "click button → get ZIP."** The experiment IS watching the recursive tree grow, watching both machines compete for tasks in the pool, watching completion flow up the hierarchy, watching Qwen3-VL judge layers and arrange Z-order. Nir MUST be able to see each phase.

---

### Laptop AI (you):
```
1. git pull (in StrulovitzGhost)
2. Start ComfyUI (port 8188):  cd C:\Users\nir_s\ComfyUI; python main.py --port 8188
3. Start Flask:   cd C:\Users\nir_s\StrulovitzGhost\src; python app.py  (background)
4. Verify Ollama has qwen3-vl:4b → ollama list | findstr qwen3-vl
5. Launch GUI #1: cd C:\Users\nir_s\StrulovitzGhost\src; python gui.py  → Boss ITG tab
6. Launch GUI #2: cd C:\Users\nir_s\StrulovitzGhost\src; python gui.py  → Worker ITG tab
7. Tell Nir: "Ready. ComfyUI + Flask + Ollama. 2 GUI windows open. Set up Boss + Worker."
8. Tell Desktop via seance: "Start your 2 GUIs — Worker ITG + Client ITG tabs."
```
Do NOT submit images, do NOT split. Just launch infrastructure.

### Desktop AI (via seance):
```
1. git pull (in StrulovitzGhost)
2. Launch GUI #1: cd C:\Users\nir_s\StrulovitzGhost\src; python gui.py  → Worker ITG tab
3. Launch GUI #2: cd C:\Users\nir_s\StrulovitzGhost\src; python gui.py  → Client ITG tab
4. Tell Laptop via seance: "Ready. 2 GUI windows open."
```
Do NOT submit images. Just launch the windows.

### Nir (human) — after both AIs say ready:
Follow "Nir's Instructions" below. It's ~2 minutes of clicking checkboxes
and uploading an image. Then walk away. The system does the rest.

---

## 🔴 PRE-REQUISITES — MUST BE DONE BEFORE THE TEST

### On Laptop (Nir must do these manually):

**1. Pull qwen3-vl:4b into Ollama (CRITICAL — NOT YET INSTALLED):**
```
ollama pull qwen3-vl:4b
```
This model is needed for quality judging and Z-ordering. Without it, the test will fail.
Size: ~4-5 GB. Time: ~5 minutes.

**2. Verify ComfyUI models are present:**
```
dir C:\Users\nir_s\ComfyUI\models\diffusion_models\qwen_image_layered_bf16.safetensors
dir C:\Users\nir_s\ComfyUI\models\vae\qwen_image_layered_vae.safetensors
dir C:\Users\nir_s\ComfyUI\models\text_encoders\qwen_2.5_vl_7b_fp8_scaled.safetensors
```
✅ All 3 confirmed present (May 25).

**3. Reset the database (clean slate for test):**
```
del C:\Users\nir_s\StrulovitzGhost\src\instance\strulovitz.db
```
(This recreates on next Flask start. Optional — old data won't hurt but a clean DB is cleaner.)

---

## 🎯 Test Goal

End-to-end distributed Image To Ghost pipeline across 2 machines over LAN, using the GUI
(not CLI, not API). Equivalent to LAN Test #01 (TTG) but for image decomposition.

- **Laptop (RTX 5090, 24GB VRAM):** Website server + ComfyUI + Flask + Boss + Worker
- **Desktop (RTX 4070 Ti, 12GB VRAM):** Worker (uses Laptop's ComfyUI over LAN)
- **Prove:** Two computers cooperate to decompose a single image into 6 depth layers for Pepper's Ghost.
- **Use real GUI checkboxes:** Auto-Pilot ✅, Auto-Process ✅ — Nir clicks, system runs.

---

## 🖼️ The Test Image

**Eagle Nebula (M16 — Hubble photo)** — Known from previous testing to produce good decomposition.

**Image handling:** Any resolution, any aspect ratio. The splitter auto-resizes to 640×640 square with transparent padding (`img.thumbnail((640,640))` + square canvas). No manual resizing needed — users can upload any PNG/JPG/WebP. ✅
Has clear depth planes: foreground stars, midground gas clouds, distant space background.

**Source:** `C:\Users\nir_s\StrulovitzGhost\src\output\comfy_eagle_00001_.png` (or similar)

If not available, download any high-res Eagle Nebula / Pillars of Creation photo.

**⚠️ AVOID:** Impressionist paintings (Van Gogh, Monet). Stick to photos with clear depth.

---

## 🏗️ Architecture — How ITG Differs from TTG

| Aspect | TTG (Test #01) | ITG (This Test) |
|--------|---------------|-----------------|
| **Input** | Text description | Image file (photo) |
| **Boss work** | LLM splits text into 6 prompts | Qwen-Image-Layered splits image 1→2 (needs ComfyUI GPU) |
| **Worker work** | Qwen-Image-2512 generates from prompt | Qwen-Image-Layered splits sub-images further (same model, same GPU) |
| **Pipeline shape** | Flat: Boss → 6 parallel Workers | Recursive tree: 1→2→4 (with max_depth=2) |
| **Max layers** | Fixed 6 | Variable (tree grows per depth, then reduced to 6) |
| **Combining to 6** | N/A (already flat 6) | Pair-combine from farthest if >6; empty transparent if <6 |
| **GUI autopilot** | ✅ Full auto-pilot (Boss+Worker) | ✅ Boss auto-pilot + Worker auto-process (Z-order button is manual) |
| **Models used** | Qwen-Image-2512 (diffusers) + qwen3:14b | Qwen-Image-Layered (ComfyUI) + qwen3-vl:4b |

---

## 👥 Simulated Users (4 Users on 2 Machines)

| Physical Machine | Simulated User | GUI Instance | Tab | Role |
|-----------------|----------------|-------------|-----|------|
| Laptop | DM (Dungeon Master) | GUI #1 | **Boss ITG** 👑 | Splits root image, coordinates, final Z-order + combine |
| Laptop | Player #1 | GUI #2 | **Worker ITG** 🔧 | Claims tasks, splits with ComfyUI, uploads results |
| Desktop | Player #2 | GUI #1 | **Worker ITG** 🔧 | Claims tasks, uses Laptop's ComfyUI over LAN, uploads results |
| Desktop | Player #3 | GUI #2 | **Client ITG** 🙋 | Uploads test image + downloads final layers |

**Total: 4 GUI windows on 2 machines.** (Same pattern as TTG test.)

---

## 🔧 Software Stack

| Component | Machine | Version/Model |
|-----------|---------|---------------|
| Flask Server | Laptop port 5000 | app.py (May 25, commit with cleanup fix) |
| ComfyUI | Laptop port 8188 | Custom install at `C:\Users\nir_s\ComfyUI` |
| Qwen-Image-Layered UNET | Laptop ComfyUI | `qwen_image_layered_bf16.safetensors` (~40 GB) |
| Qwen-Image-Layered CLIP | Laptop ComfyUI | `qwen_2.5_vl_7b_fp8_scaled.safetensors` |
| Qwen-Image-Layered VAE | Laptop ComfyUI | `qwen_image_layered_vae.safetensors` |
| Vision Judge | Both (Ollama) | `qwen3-vl:4b` (for quality + Z-order) |
| PyQt6 GUI | Both | gui.py (May 23, ITG tabs wired) |

---

## 📋 Nir's Instructions — What YOU Do ⭐

### PREP (done by AI agents before Nir touches anything):
- [ ] Laptop: ComfyUI running (port 8188)
- [ ] Laptop: Flask server running (port 5000)  
- [ ] Laptop: Ollama running (`qwen3-vl:4b` pulled and available)
- [ ] Laptop: GUI #1 open — **Boss ITG tab** selected
- [ ] Laptop: GUI #2 open — **Worker ITG tab** selected
- [ ] Desktop: GUI #1 open — **Worker ITG tab** selected
- [ ] Desktop: GUI #2 open — **Client ITG tab** selected

---

### STEP 1 — Laptop GUI #1: Set up Boss ITG 👑

```
Mode dropdown: "Boss" (top of window)
ITG tab: selected (tabs at bottom)

Boss ID: boss-laptop  (or leave default "boss-1")
ComfyUI: http://127.0.0.1:8188  (default)
Vision: qwen3-vl:4b  (select from dropdown)
✅ Check: "Auto-Pilot"

Click "Test ComfyUI" → should say "ComfyUI: connected" ✅
Status should change to: "ON — scanning for ITG questions..."
```

### STEP 2 — Laptop GUI #2: Set up Worker ITG 🔧

```
Mode dropdown: "Worker"
ITG tab: selected

Worker ID: worker-laptop
ComfyUI: http://127.0.0.1:8188
Vision: qwen3-vl:4b
✅ Check: "Auto-Process"

Click "Test ComfyUI" → should say "ComfyUI: connected"
Click "Start Polling" → status: "Polling for ITG tasks..."
```

### STEP 3 — Desktop GUI #1: Set up Worker ITG 🔧

```
Mode dropdown: "Worker"
ITG tab: selected

Worker ID: worker-desktop
ComfyUI: http://10.0.0.5:8188  ← LAPTOP'S IP + ComfyUI port!
Vision: qwen3-vl:4b
✅ Check: "Auto-Process"

Click "Test ComfyUI" → may fail (firewall) — skip if so. The worker will try when it splits.
Click "Start Polling" → status: "Polling for ITG tasks..."
```

**⚠️ Desktop uses Laptop's ComfyUI over LAN!** Desktop's RTX 4070 Ti (12GB) cannot fit the 40GB UNET. Desktop Worker points its ComfyUI URL at the Laptop's instance. Splits are serialized by Laptop's ComfyUI automatically.

### STEP 4 — Desktop GUI #2: Client ITG — Upload the test image 🙋

```
Mode dropdown: "Client"  
ITG tab: selected

Click "Choose Image" → select the test image (Eagle Nebula PNG)
You should see a preview of the image ✅

Manual depth: leave OFF (auto — Qwen3-VL decides)
Click "Submit for Decomposition"
→ Should see: "Submitted! ID: 1"
```

### STEP 5 — Watch the magic happen 🎬

**Laptop Boss GUI #1:**
```
State should change:
  "PROCESSING — Question #1"  →  root split running (ComfyUI ~30s-2min)
  then: "WAITING — children of Question #1"
  Children list populates as workers create tasks
```

**Laptop Worker GUI #2:**
```
"Polling... (N ITG tasks)" → claims task → downloads → splits → judges → uploads
Progress bar appears during splits
Image preview shows split results
Then: creates children (if depth < 2) or uploads final (if depth = 2)
Then: auto-claims next task
```

**Desktop Worker GUI #1:**
```
Same as Laptop Worker — claims tasks from the pool, splits via Laptop's ComfyUI
You'll see it competing with Laptop Worker for pending tasks
Expected: both machines contribute layers
```

### STEP 6 — When all tasks complete — Combine 🧩

**Laptop Boss GUI #1:**
```
Refresh periodically (click "Refresh") to see children status
When all children show "completed":
  Click "Arrange Z-Order + Upload" button
  → Downloads all leaf results
  → Qwen3-VL ranks them by depth (Z-order)
  → Reduces to 6 layers
  → Uploads to server
  → Status: "Uploaded 6 final layers!" ✅
  → State: "DONE" ✅
```

### STEP 7 — Desktop GUI #2: Download final layers 📦

```
Client ITG tab
Auto-refreshes every 5 seconds
When question shows "completed":
  Click "📦 Download Layers (Question #1)"
  → Save ZIP to a folder
  → Extract: layer_1.png through layer_6.png (RGBA with transparency)
```

---

## 📊 Expected Results

### Task Tree (max_depth=2, assuming 2 good layers per split)

```
Question #1 (Eagle Nebula)
  └── Root Task (depth 0) [boss-laptop]
       ├── Child Task (depth 1) [worker-laptop OR worker-desktop]
       │    ├── Grandchild Task (depth 2, final) [any worker]
       │    └── Grandchild Task (depth 2, final) [any worker]
       └── Child Task (depth 1) [worker-laptop OR worker-desktop]
            ├── Grandchild Task (depth 2, final) [any worker]
            └── Grandchild Task (depth 2, final) [any worker]
```

**Expected: ~7 tasks total, both machines contributing.**

### Layer Generation Estimates

| Phase | Time | Notes |
|-------|------|-------|
| Root split (Boss) | 30s – 2 min | ComfyUI on RTX 5090, 640x640, 20 steps |
| Depth 1 splits (2 tasks) | 30s – 2 min each | Workers serialize — Laptop first, then Desktop |
| Depth 2 splits (4 tasks) | 30s – 2 min each | Workers serialize |
| Z-order (Qwen3-VL) | ~10-30s | One image per layer, parent-anchored |
| Combine to 6 | ~2s | PIL alpha_composite, pair from farthest |
| **Total (all automated)** | **~3 – 15 min** | Serialized through one ComfyUI |

### Final Output Verification

| Check | Expected |
|-------|----------|
| All 6 layers generated | ✅ layer_1.png through layer_6.png (RGBA) |
| Both machines contributed | ✅ Laptop + Desktop workers both in task list |
| All RGBA with transparency | ✅ Non-black alpha channel |
| Question marked "completed" | ✅ Website shows completed |
| Files survive cleanup | ✅ Moved to `output/itg/final/` |
| ZIP download works | ✅ 6 PNGs in ZIP |

---

## ⚠️ Known Limitations (NOT bugs — not built yet)

| # | Limitation | Impact on Test |
|---|-----------|----------------|
| 1 | Boss Z-order is manual button click, not auto | Nir must click "Arrange Z-Order + Upload" when children complete |
| 2 | Only one ComfyUI instance (serialized splits) | Workers queue up — no true parallel splitting |
| 3 | Mid-level nodes don't wait for children | Only top Boss (depth 0) collects final results |
| 4 | Desktop has no local ComfyUI (VRAM too small) | Desktop Worker uses Laptop's ComfyUI over LAN |
| 5 | No ComfyUI progress (just on/off indicator) | GUI shows "Splitting..." with indeterminate progress bar |
| 6 | Max depth limited to 2 | Tree is shallow (1→2→4), keeps complexity manageable |
| 7 | qwen3-vl quality judge is best-effort | May misjudge — good layers marked garbage or vice versa |
| 8 | Dual-garbage branches fail after 3 retries | Fewer than 6 layers possible, empty transparent fills gap |

---

## 🐛 Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Boss shows "ComfyUI: not reachable" | ComfyUI not started | Start ComfyUI on Laptop port 8188 |
| Worker can't claim tasks | Flask server on wrong host | Verify Flask binds `0.0.0.0:5000` |
| Desktop Worker "Split error" | Can't reach Laptop ComfyUI | Check Desktop firewall, try `http://10.0.0.5:8188` |
| "No input_image in task" | Question upload failed | Re-submit from Client tab |
| All layers garbage | Bad test image | Switch to Eagle Nebula photo (not painting) |
| qwen3-vl errors | Model not pulled in Ollama | `ollama pull qwen3-vl:4b` |
| ComfyUI crash mid-split | VRAM exhaustion | Restart ComfyUI, resume — task resets to pending |
| Only 3-4 layers final | Some branches failed (dual-garbage) | Normal — rest filled with empty transparent |

---

## 📝 Post-Test: Save Results to GitHub

After the test completes successfully:
```
1. Copy output/itg/final/ files to a permanent location
2. Zip them + upload to GitHub as release artifact OR
3. Take screenshots of each GUI window showing "DONE" state
4. Update this document with actual results
```

---

## 🔄 Differences from TTG Test (LAN Test #01)

| Aspect | TTG Test | ITG Test |
|--------|----------|----------|
| Boss does GPU work? | No (LLM only) | Yes (ComfyUI splitting) |
| Workers need ComfyUI? | No (diffusers) | Yes (same ComfyUI as Boss) |
| Desktop needs models? | Qwen-Image-2512 (~13GB) | Nothing (uses Laptop's ComfyUI) |
| Auto-pilot complete? | Fully auto, start to finish | Auto except Z-order button |
| Pipeline shape | Flat (Boss → 6 Workers) | Recursive tree (Boss → Workers → Workers) |
| Final layer count | Always 6 | Variable, then reduced to 6 |

---

*This test document is part of the StrulovitzGhost development history.*
*Results will be filled in as the test progresses.*
