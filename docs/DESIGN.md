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

### Stage 1 — Single Machine 🖥️ (Current Focus)

The DM's computer does everything: receives the text description → generates 6 PNG layers → displays them. Slow but simple. One machine, one Qwen model, sequential generation.

### Stage 2 — Distributed: Private Mode 🔒🏠

The 6 players bring their gaming laptops to the DM's house and connect to the same LAN/Wi-Fi. **No internet needed.**

- **DM's computer ("The Boss")**: Splits the task — assigns 1 layer to each player's computer. At the end, collects the 6 finished PNGs and displays them.
- **Players' computers ("The Workers")**: Each generates exactly **1 PNG layer** — the same layer every time (e.g., Player 1 always renders Layer 1).
- **All 6 workers operate in parallel**, fully independent — no communication between them.
- **Speed**: ~6× faster than Stage 1 (all layers generated simultaneously).

### Stage 3 — Distributed: Public Mode 🌐🏠

Same division of labor as Stage 2, but players leave their desktop gaming PCs at home. Connection happens **over the internet**.

- Players come to the DM's house **without any computer** — just themselves.
- Their home PCs (with our software pre-installed) act as remote workers.
- Requires internet, but the architecture is identical to Private Mode.

### Stage 4 — Hierarchical Scaling 🏫🏛️ (Theoretical / Demand-Driven)

The whole structure acts as a "block" that can be stacked hierarchically:

| Level | "Boss" | "Workers" |
|-------|--------|-----------|
| Classroom | Teacher | 6 Students |
| School | Principal ("Super Queen") | 6 Teachers |
| County | Superintendent | 6 Principals |
| Country | ... | ... |

Each level works in **completely parallel and distributed** fashion. A school of 6 classrooms could produce an image where each individual flower, leaf, and blade of grass gets dedicated GPU time — detail impossible for any single cloud-based AI.

### Hardware Required Per Stage

| Stage | Machines Needed | Network |
|-------|----------------|---------|
| 1 | 1 (DM only) | None |
| 2 | 7 (DM + 6 players) | LAN (no internet) |
| 3 | 7 (DM + 6 remote players) | Internet |
| 4 | N × 7 (hierarchical) | Internet |

---

## Software Architecture

### Overview

The system is built around a **Flask web server** that acts as the central hub. All communication between entities flows through this website. The user interface is browser-based, making it accessible from any device on the network.

The desktop application is built with **PyQt6** — the same executable runs on **Windows, Linux, and macOS**. There is ONE unified application that can operate in three different modes.

### The Three Entities

The same PyQt6 application runs on every computer, but each instance is configured for one of three roles:

| Entity | Role | Where it Runs | What it Does |
|--------|------|---------------|-------------|
| **Client** 🙋 | Asks the "question" | DM's computer (or any player's) | Submits the initial text description of the scene to the website |
| **Boss** 👑 (DM) | Splits the work, coordinates | DM's computer | Reads questions from the website, breaks them into 6 layer-specific prompts, posts each as a sub-task on the website, collects finished PNGs |
| **Worker** 🔧 | Does the GPU work | Each player's computer (or same machine in Stage 1) | Polls the website for available sub-tasks, claims one, generates the PNG with Qwen-Image-2512, uploads the result |

### The Flask Website (Central Hub)

The website runs on the DM's computer using **Python Flask**. It is the ONLY communication channel — entities never talk directly to each other.

**Database: SQLite** 🗄️ — chosen because it's embedded, zero-config, and perfect for single-DM setups. The schema and all database operations are designed through **SQLAlchemy ORM**, which means switching to **MySQL** (or PostgreSQL) in the future is a simple configuration change — change one connection string, and everything else works the same. No raw SQL queries anywhere in the codebase — all database access goes through SQLAlchemy models only.

**Style Preservation** 🎨 — Every question can have an optional `style` field (e.g., "Ghibli animation", "oil painting", "pixel art"). This style is passed down the entire chain: from Client → Boss → Worker prompts → Qwen-Image generation. This ensures visual consistency across all 6 layers.

**Local LLM for Boss Splitting** 🧠 — The Boss uses a **local text LLM** (NOT a cloud AI) to break complex scene descriptions into 6 layer-specific prompts. 

> **Important:** Ollama and/or LM Studio are installed by the user independently, OUTSIDE our Miniconda environment. Our software connects to them via HTTP (`localhost:11434` for Ollama, `localhost:1234` for LM Studio). They are the user's responsibility to install and run.

Supported backends:
- **Ollama** (default) — Recommended model: `qwen3` (Qwen3.6 27B dense or Qwen3.6 35B MoE quantized)
- **LM Studio** — User's choice of any local model

The `GET /api/health/llm` endpoint checks if the chosen LLM backend is running and accessible.

The LLM is only used for text-to-prompts splitting. Image generation always uses Qwen-Image-2512 (local). **At no stage does the system rely on cloud-based AI.**

**Endpoints:**

| Endpoint | Who Uses It | Purpose |
|----------|------------|---------|
| `POST /api/question` | Client | Submit a new scene description (optional: `style`) |
| `GET /api/questions` | Boss | Poll for new unanswered questions |
| `GET /api/question/{id}` | Boss | Get a specific question's details |
| `POST /api/question/{id}/split` | Boss | Use local LLM (Ollama/LM Studio) to auto-split scene into 6 layer prompts |
| `POST /api/task` | Boss | Manually create sub-tasks (layer prompts) from a question |
| `GET /api/tasks` | Worker | Poll for available sub-tasks to claim |
| `POST /api/task/{id}/claim` | Worker | Claim a specific sub-task |
| `POST /api/task/{id}/result` | Worker | Upload the finished PNG |
| `GET /api/result/{filename}` | Anyone | Download a generated PNG |

### Polling Mechanism 🔄

Entities do NOT wait for push notifications. Instead, they **poll** the website periodically:

- **Client** → Submits question once, then polls `GET /results/{id}` until all 6 layers are ready
- **Boss** → Polls `GET /questions` every few seconds for new questions from Clients
- **Worker** → Polls `GET /tasks` every few seconds for unclaimed sub-tasks

This simple polling architecture means:
- No complex real-time connections (no WebSockets needed)
- Works perfectly over LAN (Private Mode) or internet (Public Mode)
- Workers can join/leave at any time without coordination
- The website is the single source of truth

### Network Modes

#### Private Mode 🔒 (LAN / Intranet)

The Flask website runs on the DM's computer and is accessible only on the local network.

- Players connect their laptops to the same Wi-Fi / LAN
- They open a browser and navigate to `http://<dm-ip>:5000`
- **No internet required** — works completely offline

#### Public Mode 🌐 (Internet via Cloudflared)

The Flask website is still served from the DM's computer, but **Cloudflared** ([github.com/cloudflare/cloudflared](https://github.com/cloudflare/cloudflared)) creates a secure tunnel that exposes it to the global internet — without opening any firewall ports.

- DM runs: `cloudflared tunnel --url http://localhost:5000`
- Players at home access the site via a Cloudflare-generated URL
- No port forwarding, no router configuration needed
- DM's computer remains firewalled and secure

### Important: This is NOT Real-Time ⏳

This system produces **static scenes, not live video**. Each scene takes a few minutes for the AI to generate all 6 layers. This is perfectly fine for the use case:

- The system acts like a **3D diorama** or a **custom illustrated book page** — not an action game or movie
- Fantasy tabletop RPGs (like D&D) are slow-paced — characters discuss, plan, and roleplay
- The generated images are **tailored specifically** to the group's unique characters and current situation
- It's a **bespoke illustration tool**, not a real-time rendering engine

> **Future stages** may explore faster generation, but Stage 1 intentionally embraces the "slow art" approach.

### PyQt6 Unified Application

One PyQt6 application, three modes — selectable on launch:

```
┌──────────────────────────────┐
│  Strulovitz Ghost 👻         │
│                              │
│  Select Mode:                │
│  ○ Client (Ask a question)   │
│  ○ Boss (Coordinate work)    │
│  ○ Worker (Generate images)  │
│                              │
│  Server URL: [_____________] │
│                              │
│  [ Start ]                   │
└──────────────────────────────┘
```

**Client Mode UI:**
- Text input area for pasting the scene description
- Submit button
- Progress display showing which layers are completed

**Boss Mode UI:**
- Dashboard showing incoming questions
- Text editor to split a question into 6 layer prompts
- "Post Tasks" button to publish sub-tasks
- Gallery showing completed layers as they arrive

**Worker Mode UI:**
- Status display: "Polling for tasks..."
- Shows claimed task and generation progress
- Preview of generated PNG before uploading

### Stage 1 Pipeline (Single Machine)

In Stage 1, one computer runs all three modes — or simply runs a combined "standalone" mode where the same machine plays Client, Boss, and Worker roles.

```
  ┌──────────────────────────────────────────┐
  │              Single Machine               │
  │                                          │
  │  Client ──→ Flask ──→ Boss ──→ Worker    │
  │   (UI)     (local)   (logic)   (Qwen)    │
  │                                          │
  │  Output: 6 PNG windows for drag & drop   │
  └──────────────────────────────────────────┘
```

### Stage 2+ Distributed Pipeline

```
                     ┌──────────────────┐
                     │   Flask Website  │  ← Central hub
                     │ (DM's computer)  │     on LAN or via Cloudflared
                     └──┬───┬───┬───┬──┘
                        │   │   │   │
        ┌───────────────┘   │   │   └───────────────┐
        ▼                   │   │                   ▼
  ┌──────────┐              │   │            ┌──────────┐
  │ Client   │              │   │            │ Worker 1 │  ← Polls site
  │ (DM)     │              │   │            │ (Layer 1)│     Claims task
  └──────────┘              │   │            └──────────┘     Generates PNG
                            │   │
                    ┌───────┘   └───────┐
                    ▼                   ▼
              ┌──────────┐       ┌──────────┐
              │  Boss    │       │ Worker 2 │  ... (Workers 3-6)
              │  (DM)    │       │ (Layer 2)│
              └──────────┘       └──────────┘
```

**Key principles:**
- **Client submits question** → stored on Flask website
- **Boss polls** → sees new question → splits into 6 prompts → posts as tasks
- **Workers poll** → see available tasks → claim one → generate PNG → upload result
- **Zero communication between workers** — by design
- **All 6 workers operate in parallel**, completely independent
- The Flask website is the single source of truth for all state

### Important: Image Format

All generated images MUST be **PNG with transparent backgrounds** (NOT JPG). Each layer image contains ONLY the elements that belong at that depth — everything else is transparent. This is what allows the user to see through each layer to the layers behind it.

---

## Technical Stack

### DM Computer vs Player Computers

| Role | Software Needed | AI Model |
|------|----------------|----------|
| **DM's Computer** | Flask web server, PyQt6 GUI (Client/Boss mode), Cloudflared (for Public Mode), SQLite database, **Local LLM** (Ollama or LM Studio), PIL combine for hierarchical merging | Local text LLM for splitting (Qwen3 quantized) |
| **Player's Computer** | PyQt6 GUI (Worker mode) | **Qwen-Image-2512** (the heavy GPU model) |

> In Stage 1 (single machine), one computer runs everything: Flask, PyQt6 in combined mode, and Qwen-Image-2512.

### Environment: Miniconda 🐍

All project dependencies (Python, ComfyUI, Qwen model, libraries) will be installed inside an **isolated Miniconda environment**. This protects the user's gaming PC from any bad changes.

**Why Miniconda over alternatives:**
- Handles Python + CUDA + non-Python dependencies (critical for AI/GPU work)
- Huge ML/AI community — easy to find help online
- Can pin exact package versions for stability
- Works well with uncommon GPU configurations
- **The end goal is a one-click install script** that sets everything up automatically

### AI Image Generation: Qwen-Image-2512

The Worker generates images using **Qwen-Image-2512**, a powerful local AI model. Two methods are supported — the user picks in the GUI:

| Method | How it Works | Pros | Cons |
|--------|-------------|------|------|
| **diffusers** 🐍 | Python `diffusers` library loads the model directly in our conda env | ✅ Simpler, one process ✅ Auto-downloads models from Hugging Face | ❌ Needs ~13GB VRAM (full model) ❌ No GUI workflow editor |
| **comfyui** 🎨 | ComfyUI runs as a local server (bundled in `src/comfyui/`), Worker sends HTTP requests | ✅ GGUF quantized models (fits 8-12GB) ✅ Visual workflow editor ✅ Industry standard | ❌ Two processes running ❌ Slightly more complex |

**The choice is in the GUI** — a dropdown in the Worker tab lets the user select their preferred method. ComfyUI is bundled directly in the project (cloned during `setup.bat`), with all its dependencies installed in the same conda environment.

### One-Click Setup 🪄

`setup.bat` handles everything:
1. Creates conda environment `strulovitzghost`
2. Installs Flask, PyQt6, SQLAlchemy, Pillow
3. Installs PyTorch with CUDA
4. Installs diffusers, transformers, accelerate, bitsandbytes
5. Clones ComfyUI into `src/comfyui/` and installs its requirements
6. Done! User runs `run_server.bat` + `run_gui.bat`

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

## The Big Picture: Why This Beats Cloud AI 🏆

### Scaling Advantage

Cloud-based AI (OpenAI, Google, etc.) has a fixed amount of GPU time per image. Our system scales **horizontally** — add more workers, get more detail.

| Approach | GPU time per layer | Detail Level |
|----------|-------------------|--------------|
| Cloud AI (single GPU) | ~5-10 seconds | Factory standard |
| 6 Workers (1 per layer) | ~5-10 seconds per layer | Already better (parallel) |
| 36 Workers (6 per layer) | ~30-60 seconds per layer | Massively detailed |
| 6,000 Workers (1 school) | Minutes per layer | Extreme micro-detail |

With enough workers, each individual element gets dedicated attention: every flower, every leaf, every blade of grass, every scale on the Dragonborn's skin, every thread on the Halfling's cloak.

### Limitations ⚠️

Because each layer is generated independently with no communication between workers:

- **Cross-layer effects are NOT possible:**
  - A far moon reflecting in a nearby pond ✗
  - A long shadow stretching across multiple layers when the sun is low ✗
  - Light from a campfire casting shadows on a far tree ✗

These are edge cases that rarely matter in practice. The tradeoff — near-infinite detail scaling for free — far outweighs these limitations.

### The Vision

> A free, open-source system that — given enough volunteer hardware — can produce fantasy illustrations with detail exceeding the best cloud AI in the world. All running on gamers' own PCs, in their own homes, with their own characters.

---

## Project Structure

```
StrulovitzGhost/
├── README.md              # Project overview
├── run_server.bat         # Launch Flask server (Windows)
├── run_gui.bat            # Launch PyQt6 GUI (Windows)
├── docs/
│   ├── DESIGN.md          # Full design details
│   └── EXAMPLE-SCENE.md   # D&D scene walkthrough
├── src/
│   ├── app.py             # Flask web server + REST API
│   ├── models.py          # SQLAlchemy models (SQLite, MySQL-ready)
│   ├── config.py          # Configuration (DB, LLM, paths)
│   ├── llm.py             # Local LLM integration (Ollama + LM Studio)
│   ├── gui.py             # PyQt6 unified GUI (Client/Boss/Worker)
│   ├── templates/
│   │   └── index.html     # Browser dashboard
│   ├── static/
│   │   └── style.css      # Dark theme styling
│   └── output/            # Generated PNGs (gitignored)
└── .gitignore
```
