# 🧪 LAN Test #02 — ITG Distributed on 2 Machines

**Date:** May 23, 2026 | **Status:** ⏳ READY TO PLAN | **Mode:** ITG (Image To Ghost)

---

## 🤖 AI AGENTS — START HERE ON RESTART

### Laptop AI (you):
```
1. git pull (in StrulovitzGhost)
2. Start ComfyUI with Qwen-Image-Layered:   python main.py (from ComfyUI dir, port 8188)
3. Start Flask:   python app.py (from src/, in background)
4. Start Ollama with qwen3-vl:4b (for quality judging)
5. Launch process #1:  python itg_node.py --server http://localhost:5000 --id boss-laptop --once  (Boss)
6. Launch process #2:  python itg_node.py --server http://localhost:5000 --id worker-laptop (Worker)
7. Tell Nir: "Ready. ComfyUI + Flask + Boss + Worker online."
8. Tell Desktop via seance: "Start ComfyUI on port 8188, then launch Worker node."
```
Do NOT submit images, do NOT split. Just launch infrastructure.

### Desktop AI (via seance):
```
1. git pull (in StrulovitzGhost)
2. Start ComfyUI on port 8188 (if different GPU, otherwise skip — see notes)
3. Launch Worker:  python itg_node.py --server http://10.0.0.6:5000 --id worker-desktop
4. Tell Laptop via seance: "Desktop Worker ready."
```
DO NOT submit images. Just launch infrastructure.

### Nir (human) — after both AIs say ready:
1. Open website: http://localhost:5000
2. Switch to ITG tab (or use the Client ITG tab in GUI)
3. Upload test image
4. Watch website for task tree growing
5. When all complete → Download All Layers (ZIP)
6. Inspect 6 RGBA layers

---

## Test Goal

End-to-end distributed Image To Ghost pipeline across 2 machines over LAN:
- **Laptop (RTX 5090, 24GB VRAM):** Website server + ComfyUI + Boss + Worker
- **Desktop (RTX 4070 Ti, 12GB VRAM):** Worker (optional — may share Laptop ComfyUI or run own)

Prove: Two computers cooperate to decompose a single image into 6 depth layers for Pepper's Ghost.

---

## How ITG Differs from TTG

| Aspect | TTG (Test #01) | ITG (This Test) |
|--------|---------------|-----------------|
| **Input** | Text description | Image file (photo/painting) |
| **Boss work** | LLM splits text into 6 prompts | Qwen-Image-Layered splits image 1→2 (needs ComfyUI GPU) |
| **Worker work** | Qwen-Image-2512 generates from prompt | Qwen-Image-Layered splits sub-images further (same model) |
| **Pipeline shape** | Flat: Boss → 6 parallel Workers | Recursive tree: 1→2→4→8→... (controlled by max_depth) |
| **Max layers** | Fixed 6 | Variable (tree grows per depth) |
| **Combining to 6** | N/A (already flat 6) | Pair-combine from farthest end if >6; empty transparent if <6 |
| **GUI autopilot** | ✅ Full auto-pilot | ❌ CLI-based (GUI stubs not yet wired) |
| **Models used** | Qwen-Image-2512 (diffusers) + qwen3:14b | Qwen-Image-Layered (ComfyUI) + qwen3-vl:4b |
| **Per-node GPU** | Workers only | EVERY node (Boss + all Workers) |

---

## The Test Image

**Option A: Eagle Nebula (Hubble photo)** — Known to produce good decomposition. Cosmic Pillars (M16) with clear depth planes: foreground stars, midground gas clouds, distant space background. ~600×800px.

**Option B: ISS Earth photo** — Previously attempted. 640×427px. 7 layers in ~2.5 min on RTX 4070 Ti. Output was bad (deleted). Retry with adjusted settings may work.

**Option C: Boris Vallejo "Opium Dream"** — 4 good layers confirmed. Classic fantasy art with clear foreground figure, midground elements, background.

**Option D (Recommended 🔮): A high-res photo of a complex scene** — City street with clear near/far depth, or nature scene with close subject + distant background. Qwen-Image-Layered works best with photographic depth cues.

**⚠️ AVOID:** Impressionist paintings (Van Gogh, Monet). Model was trained on Photoshop PSDs — not trained for brushstroke decomposition. Produces garbage.

**Decision:** Choose Option ___ (to be decided before test).

---

## Software

| Component | Version/Model |
|-----------|---------------|
| Flask Server | app.py (May 23, commit with cleanup fix) |
| ComfyUI | Custom install at `C:\Users\nir_s\ComfyUI` |
| Qwen-Image-Layered UNET | `qwen_image_layered_bf16.safetensors` (~40 GB) |
| Qwen-Image-Layered CLIP | `qwen_2.5_vl_7b_fp8_scaled.safetensors` |
| Qwen-Image-Layered VAE | `qwen_image_layered_vae.safetensors` |
| Vision Judge | qwen3-vl:4b (Ollama, for quality + Z-order) |
| ITG Node | `itg_node.py` CLI (poll→claim→download→split→judge→upload loop) |

---

## Infrastructure Setup (Done by AI Agents)

### Laptop AI — 4 things to start:
```
1. ComfyUI (port 8188):
   cd C:\Users\nir_s\ComfyUI
   python main.py --port 8188

2. Flask server (port 5000, minimized):
   cd C:\Users\nir_s\StrulovitzGhost\src
   python app.py

3. Ollama (should already be running):
   Verify qwen3-vl:4b is pulled → ollama list

4. Boss node (depth 0):
   cd C:\Users\nir_s\StrulovitzGhost\src
   python itg_node.py --server http://localhost:5000 --id boss-laptop --once

5. Worker node:
   cd C:\Users\nir_s\StrulovitzGhost\src
   python itg_node.py --server http://localhost:5000 --id worker-laptop
```
Total: 1 ComfyUI process, 1 Flask process, 2 ITG node processes (Boss + Worker).

### Desktop AI — 2 things to start:
```
1. ComfyUI (port 8188, optional):
   If Desktop has Qwen-Image-Layered models:
   cd C:\Users\nir_s\ComfyUI
   python main.py --port 8188

2. Worker node (points to Laptop Flask):
   cd C:\Users\nir_s\StrulovitzGhost\src
   python itg_node.py --server http://10.0.0.6:5000 --id worker-desktop
```
Note: If Desktop doesn't have ComfyUI+models (40+ GB), Desktop Worker can point to Laptop's ComfyUI at `--comfy-url http://10.0.0.6:8188`. See `--help` for CLI flags.

---

## Nir's Instructions — What YOU Do ⭐

### PREP (done by AI agents before Nir touches anything):
- [ ] Laptop: ComfyUI running (port 8188)
- [ ] Laptop: Flask server running (port 5000)
- [ ] Laptop: Ollama running (qwen3-vl:4b available)
- [ ] Laptop: Boss node started (`itg_node.py --id boss-laptop --once`)
- [ ] Laptop: Worker node started (`itg_node.py --id worker-laptop`)
- [ ] Desktop: Worker node started (`itg_node.py --id worker-desktop`)

### YOU DO — Laptop (2 things):

**Step 1 — Open the website:**
```
Browser → http://localhost:5000
```
Dashboard with "Submit New Scene" form. Switch to ITG mode if needed.

**Step 2 — Upload test image:**
```
Click "Choose Image" → select test image
Set Max Depth: 2 (default, produces up to 2²+1 = 5 layers per branch, 
                  lots of sub-tasks for workers)
Click "Submit for Decomposition"
See: "Submitted! Refresh to see it."
```

### Then watch the website (Refresh periodically):

```
Question #1 → processing → completed
  Task Tree:
    Task 1 (depth 0, Boss): processing → split into 2 → children created
      Task 2 (depth 1, Worker laptop): claimed → processing → completed
      Task 3 (depth 1, Worker desktop): claimed → processing → completed
        Task 4 (depth 2): ...
        Task 5 (depth 2): ...
  Z-Order: arranged
  Combined: 6 layers ✅
```

### When complete:
```
Refresh → see "📦 Download All Layers (ZIP)" → click → get 6 RGBA PNGs
```

---

## ⚠️ Important Notes

### Why CLI not GUI for ITG
The ITG Boss/Worker GUI tabs currently have stub buttons (show "use itg_node.py terminal interface"). The terminal interface IS fully functional — just not wired to GUI buttons yet. This test uses the CLI path which exercises the same code that will eventually be behind the GUI buttons.

### VRAM Constraints
- Qwen-Image-Layered UNET is ~40 GB. Even with heavy offloading, 12 GB GPUs struggle.
- Laptop RTX 5090 (24 GB): Can run ComfyUI comfortably
- Desktop RTX 4070 Ti (12 GB): May need Laptop's ComfyUI instance over LAN
- Only ONE ComfyUI instance needed total (2 nodes on same machine serialize automatically)

### Known Issues
- **Impressionist paintings produce garbage** — Use photos only
- **Dual-garbage retry:** If both split layers fail quality check, retries 3× then marks branch failed
- **Z-order fragility:** Qwen3-VL determines depth ordering. No programmatic backup. Human review needed.
- **Aspect ratio padding:** Extreme ratios get padded to 640×640 square (transparent padding)

---

## Results

### Boss Splitting
| Metric | Value |
|--------|-------|
| Model | Qwen-Image-Layered (BF16 via ComfyUI) |
| Max Depth | 2 |
| Time per Split | ~ |
| Quality Judge | qwen3-vl:4b (Ollama) |
| Errors | |

### Layer Generation
| Layer | Content | Worker | Time | Status |
|-------|---------|--------|------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |

**Total: 2 machines, distributed decomposition proven.**

### Task Distribution
- Laptop RTX 5090: __ tasks
- Desktop RTX 4070 Ti: __ tasks

### Final Output
- [ ] All 6 layers generated
- [ ] Both machines contributed
- [ ] All RGBA with transparency
- [ ] Question marked "completed"
- [ ] Files survive cleanup (moved to `output/itg/final/`)

### Lessons Learned
- 

---

*This test document is part of the StrulovitzGhost development history.*
*Results will be filled in as the test progresses.*
