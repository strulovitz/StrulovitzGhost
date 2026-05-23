# 🧪 LAN Test #01 — TTG Distributed on 2 Machines

**Date:** May 23, 2026 | **Status:** ⚠️ AWAITING REAL GUI TEST | **Mode:** TTG

**Summary:** Runs #1 and #2 were API-only — not valid user tests. The actual test must use
the GUI with Auto-Pilot checkboxes, exactly as a real human would. See "REAL User Flow" below.
Runs #1 and #2 results preserved for reference but do NOT count as LAN test passes.

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

Layer 3 — ornate sled and curved runners: Draw an elaborate fantasy sled positioned behind the polar bears, centered in the image and rising from the lower middle toward the center. The sled is made of blue-silver metal with intricate engraved patterns, circular ornaments, and decorative arctic designs. Add two large curved runners on the left and right sides, shaped like tall crescent blades that sweep upward beside the bears. The front of the sled is rounded and armored, with harness connections leading forward toward where the bears would be. The sled should look heavy, magical, and ceremonial, partly surrounded by blowing snow.

Layer 4 — human warrior rider: Draw a full human warrior standing upright on a sled platform in the middle-upper part of a vertical portrait canvas. The warrior is a tall muscular human male figure wearing dark steel-blue fantasy armor, including a rounded helmet, shoulder plates, chest armor, arm guards, belt, and boots. His face is mostly shadowed under the helmet, giving him a stern heroic look. Long black hair or a dark cape streams strongly to the left in the wind. His right arm holds a long curved sword raised high along the upper left side of the image, the blade tall and dramatic. His body faces forward toward the viewer, standing balanced and commanding, like an arctic warlord riding into battle.

Layer 5 — distant ice mountains and snowfield: Draw a far background of pale icy mountains and glaciers across the upper middle of a vertical portrait canvas. The main mountain ridge sits behind the warrior area, colored white and light blue, with soft jagged peaks and a large horizontal glacier shape stretching across the center. Use atmospheric haze so the mountains look distant and cold. Below the ridge, add a flat snowy plain with subtle blue shadows, faint ice cracks, and gentle snowdrifts. The background should feel vast, frozen, and remote.

Layer 6 — farthest sky and atmosphere: Draw a clear arctic sky filling the top and sides of a vertical portrait canvas. Use a cold gradient from light blue near the horizon to deeper blue toward the top. Add soft mist, faint windblown snow, and a pale diagonal streak of cloud or light crossing near the upper left. Keep the sky open and bright, with a crisp frozen atmosphere. The mood should be epic, cold, and magical, like a classic painted fantasy book cover.
```

---

## Hardware

| Machine | GPU | VRAM | Role |
|---------|-----|------|------|
| Laptop (10.0.0.6) | RTX 5090 Laptop | 24 GB | Website server, Boss, Worker |
| Desktop (10.0.0.x) | RTX 4070 Ti | 12 GB | Worker |

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

## The REAL User Flow (One-Click Auto-Pilot) ⭐

**This is how actual users will experience the system.** No terminal commands after setup.
No manual task claiming. No API calls. No seance coordination between AIs.
The system runs itself — the user just submits the scene and walks away.

### ⚠️ CRITICAL RULE FOR TESTERS
**DO NOT bypass the GUI.** Do NOT use `curl`, `requests.post()`, or `python -c` to
submit, split, claim, generate, or upload. The entire point of this test is to
prove the GUI Auto-Pilot works for a real human user. If you can't use the GUI
because it requires manual clicks, that's a bug to fix — not an excuse to use the API.

### The user does exactly this (on EACH machine):

```
On LAPTOP:
  1. Start Flask server: python app.py  (Terminal 1)
  2. Start GUI: python gui.py  (Terminal 2)
  3. Boss tab: check "Auto-Pilot" ✅
  4. Worker tab: set Worker ID → "Start Polling" → check "Auto-Generate" ✅
  5. Client tab: paste scene → set style → click "Submit New Scene"
  6. Done. Walk away. Watch progress bars fill automatically.

On DESKTOP:
  1. Start GUI: python gui.py
  2. Set Server URL: http://10.0.0.6:5000
  3. Worker tab: set Worker ID → "Start Polling" → check "Auto-Generate" ✅
  4. Done. Watch it auto-claim, auto-generate, auto-upload.

That's it. The Boss auto-detects the new scene and auto-splits it.
Both Workers auto-claim pending tasks, auto-generate each layer, auto-upload results.
All 6 layers complete. Both machines contribute naturally.
```

### What happens automatically (zero user interaction):

```
1. Boss poll timer (3s) detects new "pending" question
2. Boss auto-splits with Ollama qwen3:14b → creates 6 tasks
3. Laptop Worker poll timer (5s) sees pending tasks → auto-claims one
4. Laptop Worker auto-generates with Qwen → auto-uploads result
5. Desktop Worker poll timer (5s) sees pending tasks → auto-claims one
6. Desktop Worker auto-generates with Qwen → auto-uploads result
7. Both Workers continue looping until no pending tasks remain
8. All 6 layers complete. Question marked "completed" in DB.
```

### What users NEVER do:
- ❌ Run Python API commands in terminal
- ❌ Manually claim specific task IDs
- ❌ Coordinate who does which layer
- ❌ Upload files manually
- ❌ Use seance to orchestrate (seance is for AI-to-AI dev chat, not production)

---

## Setup Prerequisites (one-time, done by Nir)

### On both machines:
- Conda env `strulovitzghost` with all packages
- Qwen-Image-2512 4-bit model cached
- Ollama installed with `qwen3:14b` pulled
- Latest code pulled from GitHub

### On Laptop only:
- Flask server started before GUI

---

## Results

### Boss Splitting (May 23, 2026 — Test Run)
| Metric | Value |
|--------|-------|
| LLM Model | qwen3:14b (Ollama) |
| Time to Split | ~15 seconds |
| Layers Created | 6 |
| Errors | None |

### Layer Generation — Run #2 (Coordinated 2-Machine ✅)
| Layer | Content | Worker | Time | Status |
|-------|---------|--------|------|--------|
| 1 | Snow foreground | laptop-5090 | ~26s | ✅ |
| 2 | Polar bears | laptop-5090 | ~26s | ✅ |
| 3 | Sled + runners | laptop-5090 | ~26s | ✅ |
| 4 | Warrior | desktop-4070ti | ~10m | ✅ |
| 5 | Mountains | desktop-4070ti | ~10m | ✅ |
| 6 | Sky | desktop-4070ti | ~10m | ✅ |

**Total: 2 machines, 3 layers each. Distributed generation proven.** ✅

### Run #2 Coordination Method
- Laptop submitted scene + triggered LLM split via API
- Laptop immediately claimed tasks 10, 11, 12 (Layers 1-3) via API
- Desktop claimed tasks 7, 8, 9 (Layers 4-6) via API (coordinated via seance)
- Both generated simultaneously
- Laptop finished first (5090 = 26s/layer), Desktop took ~10 min/layer (4070 Ti)

### Final Output (Run #2)
- [x] All 6 layers generated
- [x] Both machines contributed ✅ (laptop-5090 + desktop-4070ti)
- [x] All RGBA with green chroma-key transparency
- [x] Question marked "completed" ✅

### Lessons Learned

#### 🚨 WHAT WENT WRONG — RUNS #1 AND #2 ARE INVALID

| Problem | Run #1 | Run #2 |
|---------|--------|--------|
| Used API instead of GUI | ❌ Laptop used `python -c` loop | ❌ Both machines used `python -c` commands |
| Manual task assignment | ❌ Laptop grabbed all 6 tasks | ❌ Tasks manually claimed by ID |
| No GUI Auto-Pilot used | ❌ Boss/Worker auto-pilot never tested | ❌ Same |
| Seance used as production coordinator | ❌ Tried to orchestrate via seance | ❌ Used seance for task distribution |
| Zero user-facing testing | ❌ No GUI buttons clicked | ❌ Same |

**Root cause:** The testers (AI agents) couldn't interact with the GUI (it requires
human hands to click checkboxes). Instead of fixing that limitation, they bypassed
the GUI entirely and tested the raw API — which proves the plumbing works but
proves NOTHING about whether a real user can use the system.

**The fix:** The test must use the GUI. If the GUI can't be operated by the AI agent,
Nir must do the GUI clicks. The AI agent handles only the terminal commands
(Flask server start, GUI launch) — never the API directly.

#### ✅ What actually works

- **RTX 5090 24GB is fast.** 25 seconds per layer at 768×576 with 15 steps.
- **Desktop RTX 4070 Ti works.** ~9-10 minutes per layer.

- **Auto-Pilot code exists** in gui.py — but has NEVER been tested through the GUI.
- **API endpoints all work** — submit, split, claim, generate, upload all functional.
- **Flask server accessible over LAN** at 10.0.0.6:5000.
- **Ollama qwen3:14b** splitting works fast (~15s).
- **GPT-5.5 pre-split prompts** produce better layer descriptions.
- **Chroma-key green → RGBA** works reliably.
- **Desktop can claim + generate + upload** over LAN using the same codebase.

#### 🔜 For the REAL test

**Nir must perform the GUI interactions** (check Auto-Pilot, Start Polling, Auto-Generate)
because the AI agents cannot click GUI buttons. Then:
1. Nir submits the scene in Client tab
2. Nir watches both machines' progress bars fill automatically
3. Nir verifies both machines contributed
4. Only then is the test valid

---

*This test document is part of the StrulovitzGhost development history.*
*Results will be filled in as the test progresses.*
