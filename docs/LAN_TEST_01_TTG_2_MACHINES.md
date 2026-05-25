# 🧪 LAN Test #01 — TTG Distributed on 2 Machines

**Date:** May 23, 2026 | **Status:** ✅ COMPLETED — REAL GUI TEST | **Mode:** TTG

---

## 🤖 AI AGENTS — START HERE ON RESTART

**You are simulating real human users. Do NOT use the API directly.**
Your ONLY job is terminal commands to start servers/GUIs. Nir clicks everything else.

### Laptop AI (you):
```
1. git pull (in StrulovitzGhost)
2. Start Flask:   python app.py   (from src/, in background)
3. Launch GUI #1: python gui.py   (from src/)  → this will be Boss tab
4. Launch GUI #2: python gui.py   (from src/)  → this will be Worker tab
5. Tell Nir: "Ready. 2 GUI windows open. Set up Boss + Worker tabs."
6. Tell Desktop via seance: "Start your 2 GUIs — Worker + Client tabs."
```
Do NOT submit scenes, do NOT split, do NOT generate. Just launch the windows.

### Desktop AI (via seance):
```
1. git pull (in StrulovitzGhost)
2. Launch GUI #1: python gui.py   (from src/)  → this will be Worker tab
3. Launch GUI #2: python gui.py   (from src/)  → this will be Client tab
4. Tell Laptop via seance: "Ready. 2 GUI windows open."
```
Do NOT submit scenes, do NOT generate. Just launch the windows.

### Nir (human) — after both AIs say ready:
Follow "Nir's Instructions" below. It's 5 minutes of clicking checkboxes
and pasting a scene. Then walk away. The system does the rest.

---

## Test Goal

End-to-end distributed Text To Ghost pipeline across 2 machines over LAN:
- **Laptop (RTX 5090, 24GB VRAM):** Website server + Boss + Worker
- **Desktop (RTX 4070 Ti, 12GB VRAM):** Worker

Prove: Two computers cooperate to generate a complete 6-layer Pepper's Ghost scene.

---

## The Scene (GPT-5.5 Pre-Split — Run #2)

Frank Frazetta's Silver Warrior — polar bears, armored warrior on sled, icy arctic mountains.

**Overall image:** A vertical fantasy illustration shows a heroic arctic scene in cold blue and white tones. Four large white polar bears charge forward through deep snow toward the viewer, pulling an ornate blue-silver sled with curved blade-like runners. A human warrior stands upright on the sled behind them, wearing dark metallic armor and a helmet, with long black hair or a cape blowing left in the wind, holding a tall curved sword raised upward. Behind the figure are pale icy mountains and a bright blue frozen sky, with blowing snow and mist giving the whole scene a dramatic, fast-moving, mythic winter atmosphere.

```
Layer 1 — closest foreground snow: Draw a vertical portrait canvas with the closest foreground made of deep powdery snow filling the bottom quarter of the image. The snow is soft, uneven, and slightly mounded, with blue-gray shadows and bright white highlights. Add kicked-up snow mist and powder clouds around the lower center and lower right, as if heavy animals have just run through it. Include a few large paw-shaped depressions and rough snow ridges near the bottom edge, making the viewer feel very close to the action.

Layer 2 — four charging polar bears: Draw four large white polar bears in the lower half of a vertical portrait canvas, running directly toward the viewer in a tight group. The bears have thick cream-white fur with blue-gray shadowing, black noses, dark eyes, and open mouths showing energy and motion. Place one bear front-left closest and slightly lower, one bear front-right with its head turned slightly left and mouth open, and two bears behind them at center and upper right, partly overlapping. Their paws are large and heavy, pushing through snow, with snow powder rising around their legs. The bears should look like powerful sled-pulling animals, facing forward and moving fast.

Layer 3 — ornate blue-silver arctic sled, angled mostly forward: Draw an elaborate fantasy arctic sled in a vertical portrait composition, placed in the center of the image. The vehicle is facing mostly toward the viewer, angled only slightly to the viewer's left, about 30 degrees from straight forward. Its front is closer to the viewer than its back, creating a strong forward-moving perspective. The sled is made of polished blue-silver metal with intricate engraved patterns, circular ornaments, swirling arctic designs, and icy decorative details. The front body is rounded and armored, with a waist-high curved guard at the front and along both sides, like a protective metal wall around the standing area. The guard rises high enough to hide a rider's legs from view. The sled has two long metal runners underneath, visible near the snow, and two large upward-curving side runners shaped like crescent blades. The side runners sweep upward on the left and right edges, with the right runner slightly more visible because of the angled perspective. The whole object should look ceremonial, heavy, magical, and fast, cutting through snow. Add blowing snow around the bottom runners and a little powder mist behind and beside the vehicle. Keep the center standing area empty, with the ornate waist-high guard clearly visible.

Layer 4 — human warrior visible from waist up, standing behind a waist-high guard: Draw a tall muscular human male warrior in the middle-upper part of a vertical portrait composition, facing forward toward the viewer. Show him from the waist upward, with his lower body hidden behind an ornate waist-high blue-silver metal guard across the lower part of the image. The guard is curved and decorated with engraved icy patterns, matching a fantasy arctic vehicle, and it covers the warrior from the waist down. The warrior stands upright and commanding, as if riding forward into battle. He wears dark steel-blue fantasy armor: a rounded helmet with a small top ornament, broad shoulder plates, a round-plated chest piece, metal bracers, leather straps, and a heavy belt visible just above the guard. His face is shadowed under the helmet, with a stern heroic expression. Long black hair or a dark cloak streams strongly to the viewer's left in the wind. One arm is raised high on the viewer's left side, holding a long curved sword that points upward into the sky; the blade is tall, narrow, and dramatic. Use cold blue highlights on the armor, strong fantasy illustration lighting, and a heroic arctic warlord mood.

Layer 5 — distant ice mountains and snowfield: Draw a far background of pale icy mountains and glaciers across the upper middle of a vertical portrait canvas. The main mountain ridge sits behind the warrior area, colored white and light blue, with soft jagged peaks and a large horizontal glacier shape stretching across the center. Use atmospheric haze so the mountains look distant and cold. Below the ridge, add a flat snowy plain with subtle blue shadows, faint ice cracks, and gentle snowdrifts. The background should feel vast, frozen, and remote.

Layer 6 — farthest sky and atmosphere: Draw a clear arctic sky filling the top and sides of a vertical portrait canvas. Use a cold gradient from light blue near the horizon to deeper blue toward the top. Add soft mist, faint windblown snow, and a pale diagonal streak of cloud or light crossing near the upper left. Keep the sky open and bright, with a crisp frozen atmosphere. The mood should be epic, cold, and magical, like a classic painted fantasy book cover.
```

---

## The Simulated Users (Who Runs What)

We have 2 physical machines simulating 4 separate users. Each user opens their own
instance of the StrulovitzGhost GUI and stays on the tab for their assigned role.

| Physical Machine | Simulated User | GUI Instance | Tab | Role |
|-----------------|----------------|-------------|-----|------|
| Laptop | DM | GUI #1 | **Boss** 👑 | Runs website + auto-splits scenes |
| Laptop | Player #1 | GUI #2 | **Worker** 🔧 | Auto-generates layers with RTX 5090 |
| Desktop | Player #2 | GUI #1 | **Worker** 🔧 | Auto-generates layers with RTX 4070 Ti |
| Desktop | Player #3 | GUI #2 | **Client** 🙋 | Submits scene + downloads final layers |

**Total: 4 GUI windows on 2 machines.**

The Client submits via the GUI's Client tab (or the website). When all 6 layers are
done, they click "Download All Layers" → selects a folder → gets `layer1.png`
through `layer6.png` with clean names. On the website, they click "📦 Download All
Layers (ZIP)" to get the same files as a ZIP.

---

## Software

| Component | Version/Model |
|-----------|---------------|
| Flask Server | app.py (May 22, commit `b134e73`) |
| PyQt6 GUI | gui.py (May 22, auto-detect models) |
| Boss LLM | qwen3:14b (Ollama, 9 GB) |
| Worker Image AI | Qwen-Image-2512 4-bit (diffusers) |
| Chroma Key | green, #00FF00 → PIL alpha |

---

## Nir's Instructions — What YOU Do (Real User Flow) ⭐

The AI agents handle terminal commands (Flask server, GUI launch). You handle
the GUI checkboxes and the website. This is exactly what a real user does.

### PREP (done by AI agent before Nir touches anything):
- [ ] Laptop: start Flask server in background (`python app.py` from src/)
- [ ] Laptop: launch 2 GUI windows:
  - [ ] `python gui.py` → Boss tab (for the DM)
  - [ ] `python gui.py` → Worker tab (for Player #1)
- [ ] Desktop: launch 2 GUI windows:
  - [ ] `python gui.py` → Worker tab (for Player #2)
  - [ ] `python gui.py` → Client tab (for Player #3, the submitter)

### YOU DO — Laptop (3 things: website + 2 GUI windows):

**Step 1 — Open the website:**
```
Browser → http://localhost:5000
```
Dashboard with "Submit New Scene" form. This is where the Client submits.

**Step 2 — GUI window #1: Set up Boss (the DM):**
```
This window is on the "Boss" tab.
Click "Detect Models" → select qwen3:14b
Check: "Auto-Pilot" ✅
Status: "ON — watching for new scenes..."
```

**Step 3 — GUI window #2: Set up Worker (Player #1 on Laptop's GPU):**
```
This window is on the "Worker" tab.
Set Worker ID: laptop-5090
Click "Start Polling"
Check: "Auto-Generate" ✅
```

**Step 4 — Submit the scene (on the website):**
```
Paste the Silver Warrior scene → Style: "Frank Frazetta fantasy art"
Click "Submit Question"
See: "Submitted! ✅ Refresh to see it."
```

### YOU DO — Desktop (2 GUI windows):

**GUI window #1 — Set up Worker (Player #2 on Desktop's GPU):**
```
Worker tab.
Set Server URL: http://10.0.0.5:5000
Set Worker ID: desktop-4070ti
Click "Start Polling"
Check: "Auto-Generate" ✅
```

**GUI window #2 — Set up Client (Player #3, the submitter):**
```
Client tab.
Set Server URL: http://10.0.0.5:5000
(This is where you'll paste the scene — or use the website at http://10.0.0.5:5000)
```

### When all 6 layers are done:

**Desktop Client GUI:** Select the completed question → click "Download All Layers" → pick a folder → gets `layer1.png` through `layer6.png`.

**OR on the website:** Refresh → see "📦 Download All Layers (ZIP)" → click → downloads `scene_X_layers.zip`.

### What you should see on the website (Refresh periodically):

```
Question #2 → processing → completed
  Layer 1: completed [laptop-5090]     📷 View
  Layer 2: completed [desktop-4070ti]  📷 View
  Layer 3: completed [laptop-5090]     📷 View
  Layer 4: completed [desktop-4070ti]  📷 View
  Layer 5: completed [laptop-5090]     📷 View
  Layer 6: completed [desktop-4070ti]  📷 View
```

3 simulated users, 2 physical machines, 2 Workers both contributing.
The website is the central hub. The Boss and Workers all poll it autonomously.
Zero manual coordination. The system works.

---

## Setup Prerequisites (one-time, already done)

### Both machines:
- Conda env `strulovitzghost` with all packages ✅
- Qwen-Image-2512 4-bit model cached ✅
- Ollama installed with `qwen3:14b` pulled ✅
- Latest code pulled from GitHub ✅

### What the AI agent does (before Nir touches anything):
- Laptop: start Flask server (`python app.py` from src/) → serves at http://10.0.0.5:5000
- Laptop: start GUI (`python gui.py` from src/)
- Desktop: start GUI (`python gui.py` from src/)

---

## Results

### ✅ REAL GUI TEST — Run #3 (May 23, 2026) 🎉

**This was the REAL test** — Nir clicked all GUI checkboxes, submitted from Desktop Client tab. Zero API usage. No AI agents touched anything. Proper user-facing flow.

### Setup (GUI Clicking by Nir)
| Machine | Window | Tab | Setup |
|---------|--------|-----|-------|
| Laptop | GUI #1 | Boss | Detect qwen3:14b → Auto-Pilot ✅ |
| Laptop | GUI #2 | Worker | ID: laptop-5090 → Polling → Auto-Generate ✅ |
| Desktop | GUI #1 | Worker | URL: 10.0.0.5:5000 → ID: desktop-4070ti → Polling → Auto-Generate ✅ |
| Desktop | GUI #2 | Client | URL: 10.0.0.5:5000 → Paste scene → Submit ✅ |

### Submission
- Submitted from Desktop Client tab (proper user flow)
- Silver Warrior — Frank Frazetta arctic fantasy scene, 6 layers
- Style: Ghibli animation

### Boss Splitting
| Metric | Value |
|--------|-------|
| LLM Model | qwen3:14b (Ollama) |
| Time to Split | ~15 seconds |
| Layers Created | 6 |
| Errors | None |

### Layer Generation

| Layer | Content | Worker | Time | Size | Status |
|-------|---------|--------|------|------|--------|
| 1 | Snow foreground | laptop-5090 | ~26s | 599 KB | ✅ |
| 2 | Polar bears | laptop-5090 | ~26s | 565 KB | ✅ |
| 3 | Sled | laptop-5090 | ~26s | 741 KB | ✅ |
| 4 | Warrior | laptop-5090 | ~26s | 680 KB | ✅ |
| 5 | Mountains | laptop-5090 | ~26s | 498 KB | ✅ |
| 6 | Sky | desktop-4070ti | ~10m | 443 KB | ✅ |

**Total: 2 machines, 5 layers Laptop (5090) + 1 layer Desktop (4070 Ti).**
**All 6 files preserved in `output/ttg/final/` after cleanup fix.** ✅

### Layer Distribution
- Laptop RTX 5090: 5 of 6 layers (~26s each, ~2 min total)
- Desktop RTX 4070 Ti: 1 layer (~10 min)
- Desktop was outpaced by faster 5090 claiming tasks rapidly

### 🐛 BUG FOUND & FIXED: Cleanup Deleted Layer Files

**Root cause:** `_cleanup_question()` used wildcard pattern `task{question_id}*` which accidentally matched task-level files when question ID collided with task IDs. When question #1 auto-completed, pattern `task1*` matched task ID 1's uploaded file (Layer 6) and silently deleted it — before Nir could download the ZIP.

**Fix (commit `b7d2a10`):**
- Replaced wildcard `glob.glob` patterns with DB-driven exact filenames
- Auto-complete now **MOVES** files from `temp/` → `final/` (preserves for ZIP download)
- Manual DELETE endpoint still permanently removes files
- Removed unused `glob` import

### Final Verification
| Check | Status |
|-------|--------|
| All 6 layers generated | ✅ |
| Both machines contributed | ✅ |
| Files survive auto-complete (in final/) | ✅ |
| ZIP download includes all 6 | ✅ |
| Submitted from Desktop Client tab | ✅ |
| Zero API usage by AI agents | ✅ |
| GUI checkboxes all clicked by Nir | ✅ |
| Seance used for AI coordination only | ✅ |

**🎯 THE DISTRIBUTED PIPELINE WORKS END-TO-END THROUGH THE GUI.**

### ❌ Previous Runs (Invalid — API-only tests)

Runs #1 and #2 used raw API calls (bypassing GUI). Proved plumbing works but tested zero user-facing features. Seance was improperly used as task coordinator.

### Lessons Learned

- **RTX 5090 24GB:** 25s/layer at 768×576. **Fast.** ⚡
- **RTX 4070 Ti 12GB:** 9-10 min/layer. Works reliably over LAN.
- **Auto-Pilot (Boss + Worker):** ✅ Proven through real GUI clicking
- **Desktop can claim + generate + upload** over LAN ✅
- **Ollama qwen3:14b** splitting: ~15s ✅
- **Chroma-key green → RGBA:** Works ✅
- **GUI is the interface:** API is plumbing only. Tests must use GUI.
- **Seance:** For AI-to-AI coordination only. Never for task distribution.

---

*This test document is part of the StrulovitzGhost development history.*
*Results will be filled in as the test progresses.*
