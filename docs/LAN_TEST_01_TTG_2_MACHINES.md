# 🧪 LAN Test #01 — TTG Distributed on 2 Machines

**Date:** May 22, 2026 | **Status:** IN PROGRESS | **Mode:** TTG

---

## Test Goal

End-to-end distributed Text To Ghost pipeline across 2 machines over LAN:
- **Laptop (RTX 5090, 24GB VRAM):** Website server + Boss + Worker
- **Desktop (RTX 4070 Ti, 12GB VRAM):** Worker

Prove: Two computers cooperate to generate a complete 6-layer Pepper's Ghost scene.

---

## The Scene

Frank Frazetta's Silver Warrior — polar bears, armored barbarian on a sled, icy mountains.

```
Layer 1, closest to the camera: In the foreground, four powerful white polar bears charge
forward through deep powdery snow, filling the lower half of the image. Their bodies overlap
tightly in a wedge formation, with heavy paws breaking through the snow, open mouths, dark
noses, and thick cream-white fur shaded with blue-gray shadows. Snow mist and soft drifting
powder surround their legs, making the scene feel cold, fast, and forceful.

Layer 2, just behind them: The bears are harnessed to an ornate fantasy sled with large
curved metal runners sweeping upward on both sides like crescent blades. The front of the
sled is decorated with intricate blue-silver engravings, circular patterns, and sculpted
metalwork, partially buried in blowing snow.

Layer 3, middle depth: Standing upright on the sled is a muscular armored warrior, centered
vertically in the composition, wearing dark steel-blue armor with round plates, belts, and
fur or leather details. The warrior holds a long curved sword raised high on the left side
of the image, and a dark cape or long black hair streams dramatically to the left in the wind.

Layer 4, behind the warrior: The upper body and helmet are silhouetted against the pale sky;
the helmet has a rounded crown and small ornament, while the face is shadowed and stern,
giving the figure a mythic barbarian or arctic warlord feeling. The sword's blade is dark
bronze or steel, tapering upward into the sky, creating a strong diagonal line.

Layer 5, distant background: Behind the rider are pale blue-white snowfields and jagged icy
mountains, with one large glacier-like ridge stretching horizontally across the upper center,
softened by atmospheric haze. The landscape is minimal and frozen, with faint cracks and
ridges in the ice.

Layer 6, farthest depth and atmosphere: The sky is a clear cold gradient of light to medium
blue, with subtle mist, windblown snow, and a faint diagonal streak of cloud or light near
the upper left. The overall composition is vertical, painted in a classic fantasy illustration
style, dominated by icy blues, whites, silver metal, dramatic motion, and a heroic central
silhouette advancing directly toward the viewer.
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

### Boss Splitting
| Metric | Value |
|--------|-------|
| LLM Model | qwen3:14b |
| Time to Split | ~34 seconds |
| Layers Created | 6 |
| Errors | None |

**Note:** Initially tried `qwen3.6:27b` (thinking/reasoning model). It timed out at 300 seconds — too slow for API automation on RTX 5090 24GB. Reasoning models generate long `&lt;think&gt;` traces before responding. For scene splitting, a standard dense model like `qwen3:14b` is much faster and sufficient. **Do NOT use thinking models for Boss API tasks — use non-reasoning models.**

### Layer Generation
| Layer | Content | Worker | Time | Status |
|-------|---------|--------|------|--------|
| 1 | Polar bears | ___ | ___ | ⬜ |
| 2 | Sled | ___ | ___ | ⬜ |
| 3 | Warrior | ___ | ___ | ⬜ |
| 4 | Warrior upper | ___ | ___ | ⬜ |
| 5 | Mountains | ___ | ___ | ⬜ |
| 6 | Sky | ___ | ___ | ⬜ |

### Final Output
- [ ] All 6 layers generated
- [ ] All RGBA with transparency
- [ ] Green screen correctly keyed
- [ ] Scene Viewer opens all 6 windows
- [ ] Layers visually stack correctly

### Lessons Learned
- **Thinking models are too slow for API Boss tasks.** `qwen3.6:27b` took >300s (timed out) because of chain-of-thought. `qwen3:14b` (standard dense) completed in 34s. Use non-reasoning models for Boss LLM tasks.
- **Model auto-detection in GUI is essential.** Without the "Detect Models" button, users would need to manually type model names from Ollama CLI. Fixed in commit `c6ac121`.
- ___

---

*This test document is part of the StrulovitzGhost development history.*
*Results will be filled in as the test progresses.*
