# StrulovitzGhost 👻

A new way to render graphics for fantasy games — creating true depth illusions using multiple semi-transparent layers, inspired by Pepper's Ghost.

## What is it?

Strulovitz Ghost is a **multi-layer Pepper's Ghost** effect: instead of one reflective surface, the user looks through **6 half-transparent layers** arranged in depth, creating a holographic-like 3D illusion. The software projects precisely calibrated images onto flat monitors, and each image reflects off a transparent layer at 45°, building a scene with real physical depth — from 20 cm to 2 meters away from the viewer's eyes.

## How it works

### Physical Setup (DIY)

- **3 gaming monitors** laid flat on a table, like floor tiles in a line
- **6 reflective layers** made from CD/DVD cases, opened at 45° angles (2 per monitor)
- The user sits at the head of the table and looks through all 6 layers
- Each layer is half-transparent — you see through it to the layers behind

### Software

- **AI generates 6 PNG images** (one per layer), each with transparent background
- Each PNG opens in its own window — user drags to correct position
- Like a **3D diorama / custom illustrated book page** — not real-time action

### Quick Example: D&D Night Camp

> The DM pastes "The group makes camp in a moonlit forest clearing..." → AI generates: night sky (far), mountains, forest, characters around campfire, close-up framing with an owl and rabbit (near).

## Future Stages

| Stage | Description |
|-------|-------------|
| **1** 🖥️ | Single machine — DM's PC does everything |
| **2** 🔒 | Private Mode — 6 players' laptops on LAN, one layer each (no internet) |
| **3** 🌐 | Public Mode — 6 players' home PCs over internet, parallel generation |
| **4** 🏫 | Hierarchical scaling — classrooms → schools → counties → countries |

> The vision: scale horizontally with volunteer hardware to achieve detail **exceeding cloud AI** — for free.

👉 **Full design**: [docs/DESIGN.md](docs/DESIGN.md)
👉 **Detailed scene walkthrough**: [docs/EXAMPLE-SCENE.md](docs/EXAMPLE-SCENE.md)

## Architecture

Three entities, one unified app, one central website:

| Entity | Role | UI |
|--------|------|----|
| **Client** 🙋 | Submits the scene description | PyQt6 |
| **Boss** 👑 | Splits into 6 layer prompts, coordinates | PyQt6 |
| **Worker** 🔧 | Polls for tasks, generates PNG with Qwen | PyQt6 |

All communication flows through a **Flask website** (the central hub) via simple polling — no WebSockets, no direct connections between workers. Works over LAN (Private Mode) or internet via **Cloudflared** tunnel (Public Mode).

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 🐍 |
| Desktop UI | PyQt6 (cross-platform: Win / Mac / Linux) |
| Web Server | Flask (central hub) |
| Database | SQLite via SQLAlchemy (easy switch to MySQL for scale) |
| AI Model | [Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512) (local, free) |
| AI Merge | [Qwen-Image-Edit](https://huggingface.co/Qwen/Qwen-Image-Edit) (DM's computer) |
| Public Tunnel | [Cloudflared](https://github.com/cloudflare/cloudflared) (no firewall ports needed) |
| Environment | Miniconda (isolated, one-click install) |

## Status

🚧 **Planning / Design Phase** — All specifications being documented. Code development not yet started.

## License

TBD
