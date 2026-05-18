# Strulovitz Ghost — Design Document 👻

## Inspiration: Pepper's Ghost

[Pepper's Ghost](https://en.wikipedia.org/wiki/Pepper%27s_ghost) is a classic illusion technique using a sheet of glass (or transparent plastic) at a 45° angle. The viewer sees both the reflection from the glass and whatever is behind it, creating a ghostly, semi-transparent apparition.

**Strulovitz Ghost extends this idea to multiple layers** — not just one, but six layers arranged in depth, each one behind the other.

---

## The Physical Setup (DIY — Done by the User)

### Monitors

- **3 gaming monitors** are laid flat on a table, side by side in a line (like 3 floor tiles)
- Each monitor faces upward (screen towards the ceiling)
- The user's gaming PC must support at least 3 monitor outputs (standard on modern NVIDIA/AMD cards)

### Reflective Layers

- Each layer is made from a **transparent CD or DVD plastic case**, opened and positioned at a **45° angle**
- The case is fixed in place using a **toothpick and adhesive tape**
- **2 layers per monitor**:
  - One on the **near side** of the monitor (closer to the user)
  - One on the **far side** of the monitor (farther from the user)
  - Both layers face the same direction

### Total Configuration

| Monitor | Layer Position | Layer # |
|---------|---------------|---------|
| Monitor 1 (closest to user) | Near side | Layer 1 |
| Monitor 1 (closest to user) | Far side  | Layer 2 |
| Monitor 2 (middle)          | Near side | Layer 3 |
| Monitor 2 (middle)          | Far side  | Layer 4 |
| Monitor 3 (farthest)        | Near side | Layer 5 |
| Monitor 3 (farthest)        | Far side  | Layer 6 |

**Total: 3 monitors × 2 layers = 6 layers**

---

## The Viewing Experience

The user sits at the **head of the table**, looking through all 6 layers stacked in depth.

- **Layer 1** (closest): ~20 cm from the user's eyes — appears very near
- **Layer 6** (farthest): ~2 meters from the user's eyes — appears very far
- Each layer is **half-transparent**, so the user can see through it to all layers behind it

The result is a scene with **real physical depth** — not simulated on a flat screen, but actually occupying 3D space between 20 cm and 2 meters from the viewer.

---

## Software Role (What We Build Here)

The software's job is to **calculate and render the correct image for each of the 6 layers**. Each monitor receives two images (one for its near layer, one for its far layer). The images must account for:

- The 45° reflection angle
- The transparency of each layer
- The depth position of each layer
- What the user should see through each layer at their specific viewing angle

---

## Future Stages (Planned)

| Stage | Description |
|-------|-------------|
| **Stage 1** | Text-to-6-Layers — DM pastes scene description, AI generates 6 PNG layers with transparent backgrounds |
| **Stage 2** | Real-time rendering — dynamic graphics that update per frame as the game progresses |
| **Stage 3** | Distributed computing — combine computing power from multiple players' gaming PCs over the internet |
| **Stage 4** | Game engine integration — hook into existing fantasy games for automatic scene capture |

---

## Software Architecture

### Overview

The user (typically a Dungeon Master for D&D or similar tabletop RPG) runs a **browser-based GUI** — not a CLI. This is important for ease of use and for future phases where computing will be distributed across the internet between multiple players' machines.

### Important: This is NOT Real-Time ⏳

This system produces **static scenes, not live video**. Each scene takes a few minutes for the AI to generate all 6 layers. This is perfectly fine for the use case:

- The system acts like a **3D diorama** or a **custom illustrated book page** — not an action game or movie
- Fantasy tabletop RPGs (like D&D) are slow-paced — characters discuss, plan, and roleplay
- The generated images are **tailored specifically** to the group's unique characters and current situation
- It's a **bespoke illustration tool**, not a real-time rendering engine

> **Future stages** may explore faster generation, but Stage 1 intentionally embraces the "slow art" approach.

### Stage 1 Pipeline

```
DM types/pastes scene description
        │
        ▼
  ┌─────────────┐
  │  Text Parser │  ← Breaks scene into depth layers
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │  AI Generator│  ← Qwen-Image-2512 (local, free)
  └─────────────┘
        │
        ▼
  6 PNG files (transparent backgrounds)
  Each = one depth layer
        │
        ▼
  Each PNG opens in its own window
  User drags each window to correct monitor position
```

### Important: Image Format

All generated images MUST be **PNG with transparent backgrounds** (NOT JPG). Each layer image contains ONLY the elements that belong at that depth — everything else is transparent. This is what allows the user to see through each layer to the layers behind it.

---

## Technical Stack

### Environment: Miniconda 🐍

All project dependencies (Python, ComfyUI, Qwen model, libraries) will be installed inside an **isolated Miniconda environment**. This protects the user's gaming PC from any bad changes.

**Why Miniconda over alternatives:**
- Handles Python + CUDA + non-Python dependencies (critical for AI/GPU work)
- Huge ML/AI community — easy to find help online
- Can pin exact package versions for stability
- Works well with uncommon GPU configurations
- **The end goal is a one-click install script** that sets everything up automatically

### AI Image Generation: Qwen-Image-2512

We use a **free, local AI model** (not a cloud-based service):

- **Model**: [Qwen/Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512) on Hugging Face
- **Why local?** No API costs, works offline, privacy for the user's game content

> **Note: What we are NOT using** — The "ordinary" cloud-based approach would use [OpenRouter](https://openrouter.ai) with models like OpenAI's GPT-5.4 Image 2 or Google's Nano Banana 2 (Gemini 3.1 Flash Image Preview). We document this for comparison but our system uses the free local approach instead.

### Two Integration Methods (Both Supported)

Our software will support BOTH methods for running Qwen-Image-2512:

#### Method 1: ComfyUI with GGUF (Recommended for Consumer GPUs) 🎨

Uses quantized GGUF models to significantly lower VRAM/RAM requirements.

1. **Install ComfyUI** — a node-based interface for AI image generation
2. **Download quantized GGUF model** — from the [Unsloth Qwen-Image-2512-GGUF](https://huggingface.co/unsloth/Qwen-Image-2512-GGUF) repository. The **Q4_K_M** variant is recommended (~13 GB combined memory)
3. **Download VAE and CLIP encoders** — from the base [Qwen/Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512) collection
4. **Load a community GGUF workflow JSON** — drag-and-drop onto the ComfyUI canvas

#### Method 2: Python Hugging Face Diffusers 🐍

Direct Python integration for NVIDIA GPU users:

```bash
pip install -U diffusers transformers accelerate torch
```

```python
import torch
from diffusers import DiffusionPipeline

model_id = "Qwen/Qwen-Image-2512"
pipe = DiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="cuda"
)

prompt = "A futuristic city skyline at sunset, cyberpunk aesthetic"
image = pipe(prompt).images[0]
image.save("qwen_generated.png")
```

#### Hardware Requirements

| Setup | VRAM/RAM Needed |
|-------|----------------|
| Full model (unquantized) | ~20+ GB |
| GGUF Q4_K_M (recommended) | ~13-14 GB combined |
| With Qwen-Image-Lightning LoRA | 4-8 steps instead of 50 (much faster) |

The user's gaming PC with a modern NVIDIA/AMD GPU (capable of 3 monitors) should handle the GGUF version comfortably.

---

## D&D Use Case

### The Game Group (Our Example Characters)

The group consists of **7 friends** — 6 players + 1 Dungeon Master (DM):

| # | Character | Class | Gender | Personality |
|---|-----------|-------|--------|-------------|
| 1 | Tiefling | Fighter | Girl | Sharpening her sword, combat-ready |
| 2 | Dragonborn | Wizard | Guy | Memorizing spells from his magic book |
| 3 | Dwarf | Cleric | Guy | Argumentative, devout |
| 4 | Halfling | Thief | Guy | Argumentative, mischievous |
| 5 | Elf | Paladin | Girl | Gossiping, laughing |
| 6 | Human | Druid | Girl | Gossiping, laughing, nature-attuned |

### How the DM Uses the System Today (Without Strulovitz Ghost)

1. DM types the current game situation into an AI (local like LM Studio, or cloud-based — choice of AI doesn't matter to our system)
2. AI returns a **text description** of the new scene: surroundings, character actions, enemies, etc.
3. This is all text — no visuals

### How the DM Uses Our System (Stage 1)

1. DM **copy-pastes the AI's text description** into our browser-based GUI
2. Our system **parses the text** and determines what belongs at each depth layer
3. Our system generates **6 PNG images** (one per layer), each with transparent background
4. Each PNG opens in its own **separate window**
5. The user **drags each window** to the correct position on the correct monitor
6. Optional: User can toggle **number overlays** (1-6) on each image to verify correct placement

> 📖 Full step-by-step example: see [EXAMPLE-SCENE.md](EXAMPLE-SCENE.md)

---

## Project Structure

```
StrulovitzGhost/
├── README.md              # Project overview
├── docs/
│   ├── DESIGN.md          # This document — full design details
│   └── EXAMPLE-SCENE.md   # Detailed D&D scene walkthrough
├── src/                   # Source code (Python)
│   └── ...
└── ...
```
