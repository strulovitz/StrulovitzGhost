# 🧠 Nir's Vision — May 22, 2026

**This document captures Nir's full explanation of how StrulovitzGhost should work.**
It is preserved here so nobody (AI or human) has to explain it again.

---

## The Two Modes

StrulovitzGhost is **ONE PyQt6 program with TWO tabs:**

| Tab | Name | Function | Input → Output |
|-----|------|----------|----------------|
| Tab 1 | **Text To Ghost (TTG)** | Scene Generator | Text prompt → 6 RGBA layers |
| Tab 2 | **Image To Ghost (ITG)** | Fine Art Decomposer | Painting image → 6 RGBA layers |

In each tab there is a dropdown to choose user type: **Client / Boss / Worker**.
This dropdown is **synchronized** between tabs — change in TTG, it changes in ITG too.

The website/platform operator does NOT use this software. They only run the Flask server.
They are NOT one of the three user types.

---

## User Types (Same for Both Modes)

| User | Role |
|------|------|
| **Client** | Submits the job (text for TTG, image for ITG). Gets the final 6 layers. |
| **Boss** | Splits work, creates sub-tasks, judges quality, combines results. |
| **Worker** | Does the actual GPU-heavy work (generation or decomposition). |

---

## File Naming Convention

Every image file tracks its full ancestry path:

```
task_{id}.png                      ← Original painting (the full job)
task_{id}_01.png                   ← 1st teacher's part
task_{id}_01_02.png                ← 2nd student of 1st teacher
task_{id}_01_02_03.png             ← 3rd sub-student of that student
```

Each underscore-separated number represents one level of the hierarchy.
Example: `task_42_03_01_05.png` means:
- Task #42 (42nd painting they're decomposing)
- Teacher #3's portion
- Student #1 of teacher #3
- Sub-student #5 of student #1

This naming makes it trivial for the system to track who made what at every level.

---

## TEXT TO GHOST (TTG) — The "Clean" Mode

This is the **original concept** the entire project was designed for.

### The Flow

```
CLIENT: submits text prompt
    ↓
BOSS (Manager): splits text into 6 rough layer descriptions using Qwen LLM
    ↓ (gives each to a Teacher)
TEACHER (Sub-boss): splits EACH rough description into 6 detailed descriptions
    ↓ (gives each to a Student/Worker)
WORKER (Student): generates 1 image using Qwen-Image-2512
    ↓ (uploads result to website)
TEACHER: downloads all 6 student images, mechanically combines (PIL)
    ↓ (uploads combined classroom result to website)
MANAGER: downloads all 6 teacher results, mechanically combines (PIL)
    ↓ (uploads final 6-layer scene to website)
CLIENT: downloads the 6 layers → displays on physical Pepper's Ghost setup
```

### Key Principles
- **Bosses only THINK and WRITE TEXT** — no image generation
- **Workers only DRAW** — using Qwen-Image-2512 on their own GPU
- **Combining is mechanical** — PIL alpha_composite, no AI needed
- **Parallel:** All workers at the same level work simultaneously
- **Distributed:** No worker depends on another worker's result
- **Scalable:** School → classrooms → students (recursive hierarchy)

### The Hierarchy

```
MANAGER (Boss Level 2)
    ├── TEACHER #1 (Boss Level 1)
    │   ├── Student #1 (Worker)
    │   ├── Student #2 (Worker)
    │   └── ... (up to N students)
    ├── TEACHER #2 (Boss Level 1)
    │   └── ...
    └── ... (up to N teachers)
```

- Manager splits the SCENE into 6 PARTS
- Each Teacher splits one PART into 6 SUB-PARTS
- Each Student draws one SUB-PART
- Teachers combine 6 student images → 1 classroom image
- Manager combines 6 classroom images → final 6-layer scene

### Example: D&D Night Camp
1. Manager: "Night camp scene" → 6 rough layer descriptions (sky, forest, campfire, etc.)
2. Teacher #1: "Night sky layer" → 6 sub-descriptions (moon, stars, clouds, etc.)
3. Students draw: moon.png, stars.png, clouds.png, etc.
4. Teacher #1 combines → sky_layer.png
5. Manager combines all 6 → final scene

---

## IMAGE TO GHOST (ITG) — The "Messy" Mode

This is NOT a clean demonstration of the architecture. It's a **practical hack**
made possible because we already built the physical infrastructure and software.
Weak computers cooperate to achieve what one strong computer can do.

### Why "Messy"

**Qwen-Image-Layered does NOT allow fine-grained control.** You cannot tell it:
- "Extract only the far half of this painting"
- "Extract only the close objects"

It doesn't work that way. The model decides autonomously what goes in each layer.

Therefore:
- **EVERY node (including bosses) must have Qwen-Image-Layered** — because splitting IS the work
- **EVERY node must have Qwen3-VL** — to judge if a resulting layer is good or garbage
- **Bosses do actual GPU work** — unlike TTG where bosses only think

### The Flow

```
CLIENT: uploads painting image
    ↓
BOSS (Manager): splits 1→2 layers using Qwen-Image-Layered
    ↓ (Qwen3-VL judges: keep good layers, discard garbage)
    ↓ (passes good layers to Teachers via website)
TEACHER (Sub-boss): splits each received layer 1→2 more layers
    ↓ (Qwen3-VL judges: keep/discard)
    ↓ (passes surviving layers to Students via website)
WORKER (Student): splits 1→2 layers
    ↓ (Qwen3-VL judges: keep/discard)
    ↓ (uploads good results to website)
[On the way back UP:]
TEACHER: arranges student results by Z-depth (farthest → closest)
    ↓ (uploads Z-order info to website)
MANAGER: arranges teacher results by Z-depth
    ↓ REDUCES to 6 layers (pair-combine from farthest)
    ↓ (uploads final 6-layer scene to website)
CLIENT: downloads the 6 layers → displays on physical Pepper's Ghost setup
```

### Key Principles
- **Every node splits images** — there are no "think-only" bosses
- **Every node judges quality** — using Qwen3-VL to detect solid-color/blurry/garbage layers
- **Workers ARE bosses** — just without underlings ("bosses without children")
- **On the way up: only arrange, don't combine** — until the top boss
- **Top boss reduces to 6** — pairing from farthest (minimal parallax) toward closest
- **If <6 layers:** populate closest layers with actual images, farthest layers are empty/transparent

### Qwen3-VL Quality Gate

At every level, after splitting, Qwen3-VL examines each resulting layer:
- ✅ **Good:** Contains recognizable content → pass down for further splitting
- ❌ **Garbage:** Solid color, blurry, incomprehensible → discard

This prevents the system from wasting GPU time splitting meaningless noise.
It also determines when to stop splitting (nothing left worth splitting).

### Depth Control (GUI)

A slider + checkbox in the ITG tab:
- **Checkbox OFF (default):** Qwen3-VL decides depth autonomously at each boss level
- **Checkbox ON:** The Client sets a manual `max_depth` via the slider

---

## Combining Rules (8→6, or N→6)

Always combine from **FARTHEST** to **closest**:

1. Farthest layers have minimal parallax — combining them doesn't destroy 3D illusion
2. Closest layers have strong parallax — NEVER combine them
3. Combine in pairs, starting with the two farthest
4. Repeat until 6 layers remain

```
Given N layers (N > 6), numbered 1=farthest(sky) to N=closest(foreground):

Step 1: Combine Layer N + Layer (N-1) → New layer (farthest combined)
Step 2: Combine Layer (N-2) + Layer (N-3) → Next combined
...
Stop when 6 layers remain.
```

**If N < 6:** Closest layers get the actual images. The remaining (farthest) layers are empty transparent PNGs.

---

## Database Design

### Shared Tables
- `questions` table with `type` field: `"TTG"` or `"ITG"`
- `tasks` table with additional fields: `depth`, `max_depth`, `parent_task_id`

### File Storage
- **NO image blobs in the database.** Period.
- Database stores: `filename`, `filepath`
- All image files live on the website computer's disk
- When a job is complete and the client has downloaded results:
  - Intermediate files are DELETED
  - Only the final 6 layer files remain
- This prevents disk-space death from accumulated temp files

---

## Testing Plan

### Test 1: LAN (Both Machines)
- Website (Flask) runs on **Laptop**
- Laptop (RTX 5090 24GB) acts as Manager + Worker
- Desktop (RTX 4070 Ti 12GB) acts as Worker
- Both poll the same Flask server over LAN
- Split one painting together

### Test 2: Internet via Cloudflared
- Website (Flask) runs on **Desktop**
- Cloudflared tunnel exposes it to the real internet
- Laptop connects over the internet as a Worker
- Both split one painting together
- Proves distributed architecture works over the real internet

---

## What We Have vs What We Need

| Component | TTG Status | ITG Status |
|-----------|------------|------------|
| GUI with tabs | ❌ Single mode only | ❌ Not started |
| User-type dropdown | ✅ Client/Boss/Worker | ❌ Not started |
| Flask server | ✅ 9 endpoints | ❌ Needs new endpoints |
| Database tables | ✅ questions/tasks | ❌ Needs type/depth/parent fields |
| LLM splitting (Qwen) | ✅ llm.py | ❌ Not needed (use Qwen-Image-Layered) |
| Qwen-Image-2512 generation | ✅ generator.py | ❌ Not needed (use Qwen-Image-Layered) |
| Qwen-Image-Layered split | ❌ Not used in TTG | ❌ Needs ComfyUI integration |
| Qwen3-VL quality judge | ❌ Not used | ❌ Needs Ollama/LM-Studio integration |
| Recursive hierarchy | ❌ Not coded | ❌ Not coded |
| Chroma-key | ✅ chroma_key.py | ❌ Not needed (model outputs RGBA) |
| Layer combining (PIL) | ✅ combine.py | ✅ Reuse combine.py |
| File upload/download | ✅ Basic | ❌ Needs multi-file, recursive |
| Session/task cleanup | ❌ Not coded | ❌ Not coded |

---

*This document was dictated by Nir to Laptop AI on May 22, 2026.*
*It should be read alongside `docs/TEXT_TO_GHOST_DESIGN.md` and `docs/IMAGE_TO_GHOST_DESIGN.md`.*
