# 🧪 LAN Test #01 — TTG Distributed on 2 Machines

**Date:** May 23, 2026 | **Status:** RUN #2 IN PROGRESS | **Mode:** TTG

**Note:** Run #1 was solo Laptop (RTX 5090 too fast). Run #2 uses GPT-5.5 pre-split prompts and coordinated 2-machine generation.

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

## Step-by-Step Instructions

### Step 1: Laptop — Pull Boss Model
```powershell
ollama pull qwen3:14b
```

### Step 2: Laptop — Start Flask Website (Terminal 1)
```powershell
cd C:\Users\nir_s\StrulovitzGhost\src
C:\Users\nir_s\miniconda3\envs\strulovitzghost\python.exe app.py
```
Wait for: `Running on http://127.0.0.1:5000`

### Step 3: Laptop — Open GUI (Terminal 2)
```powershell
cd C:\Users\nir_s\StrulovitzGhost\src
C:\Users\nir_s\miniconda3\envs\strulovitzghost\python.exe gui.py
```

### Step 4: Laptop — Client: Submit Scene
1. Tab: "Text To Ghost" | Role: "Client"
2. Paste the Silver Warrior scene description (above)
3. Click **Submit New Scene**
4. Note Question ID: ___

### Step 5: Laptop — Boss: Split Scene into 6 Layers
1. Tab: "Text To Ghost" | Role: "Boss"
2. Click **Detect Models** → select `qwen3:14b`
3. Click **Refresh** → select the new question
4. Click **Auto-Split with LLM**
5. Wait for thinking model (~60-120 sec)
6. Verify 6 layers appear in tasks list

### Step 6: Laptop — Worker: Generate Layer
1. Tab: "Text To Ghost" | Role: "Worker"
2. Click **Start Polling**
3. Click a task to claim it
4. Click **Generate with Qwen AI**
5. Wait ~9 minutes
6. Click **Upload Result PNG**

### Step 7: Desktop — Worker: Generate Layer
1. Open GUI on Desktop
2. Set Server URL to: `http://10.0.0.6:5000`
3. Tab: "Text To Ghost" | Role: "Worker"
4. Click **Start Polling**
5. Claim a different task
6. Click **Generate with Qwen AI**
7. Wait ~9 minutes (RTX 4070 Ti)
8. Click **Upload Result PNG**

### Step 8: Repeat Steps 6-7
Both machines claim remaining tasks until all 6 layers generated.

### Step 9: Client — Download Final Scene
1. Role: "Client"
2. Click **Refresh**
3. Question status should show "completed"
4. Download all 6 layers

### Step 10: Open in Scene Viewer
1. Role: "Viewer"
2. Select the scene
3. Click **Open Layer Windows**
4. Verify all 6 layers display correctly

---

## Results

### Boss Splitting (May 23, 2026 — Test Run)
| Metric | Value |
|--------|-------|
| LLM Model | qwen3:14b (Ollama) |
| Time to Split | ~15 seconds |
| Layers Created | 6 |
| Errors | None |

### Layer Generation — Run #2 (Coordinated 2-Machine)
| Layer | Content | Worker | Time | Status |
|-------|---------|--------|------|--------|
| 1 | Snow foreground | ___ | ___ | ⬜ |
| 2 | Polar bears | ___ | ___ | ⬜ |
| 3 | Sled + runners | ___ | ___ | ⬜ |
| 4 | Warrior | ___ | ___ | ⬜ |
| 5 | Mountains | ___ | ___ | ⬜ |
| 6 | Sky | ___ | ___ | ⬜ |

### Distribution Plan (Run #2)
- **Laptop RTX 5090:** Layers 1, 2, 3 (foreground complex: snow, bears, sled)
- **Desktop RTX 4070 Ti:** Layers 4, 5, 6 (background: warrior, mountains, sky)
- **Strategy:** Laptop claims tasks 1-3 manually after split, Desktop auto-gen claims 4-6.
  Both generate SIMULTANEOUSLY.

### Final Output (Run #2)
- [ ] All 6 layers generated
- [ ] Both machines contributed (Desktop ≠ 0 layers)
- [ ] All RGBA with transparency
- [ ] Question marked "completed"

### Lessons Learned
- **RTX 5090 24GB is a BEAST.** 25 seconds per layer at 768×576 with 15 steps. Desktop RTX 4070 Ti takes ~9 minutes per layer. The 5090 generated all 6 layers before Desktop could claim one.
- **For distributed testing:** Laptop should take only 1-2 layers (or none) to leave work for Desktop. Or increase steps/resolution on Laptop to slow it down.
- **Auto-Pilot feature built and proven.** Boss auto-detects new scenes, Workers auto-claim+generate+upload. The system can now run fully automatically — submit scene and walk away.
- **Chroma-key quality:** 22-76% green pixels keyed per layer. Subject complexity inversely correlated with key ratio (simple sky=22%, complex warrior=76%).
- **Thinking models are too slow for API Boss tasks.** `qwen3.6:27b` took >300s (timed out) because of chain-of-thought. `qwen3:14b` (standard dense) completed in 15s. Use non-reasoning models for Boss LLM tasks.
- **Model auto-detection in GUI is essential.** Without the "Detect Models" button, users would need to manually type model names from Ollama CLI. Fixed in commit `c6ac121`.
- **Auto-Pilot implementation:** 95 lines of GUI code, zero API changes, fully backward-compatible. Boss auto-pilot polls every 3s for new pending scenes. Worker auto-generate chains claim→generate→upload in a continuous loop.

---

*This test document is part of the StrulovitzGhost development history.*
*Results will be filled in as the test progresses.*
