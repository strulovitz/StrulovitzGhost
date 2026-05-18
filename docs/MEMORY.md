# 🧠 Project Memory 🧠

Preserved context, decisions, and direction.

---

## Current State (May 2026)

### StrulovitzGhost — Active Development (Stage 1: Single Machine)

**What works end-to-end:**
- Flask server (`src/app.py`) — 9 REST endpoints, all tested
- SQLite DB via SQLAlchemy (`src/models.py`) — Question → Tasks pipeline, 3-state status (pending/claimed/completed), MySQL-ready
- PyQt6 GUI (`src/gui.py`) — 3-mode unified app (Client/Boss/Worker), dark theme, QThread-based generation, model downloader buttons
- Local LLM scene splitting (`src/llm.py`) — Ollama or LM Studio, structured 6-layer JSON output
- Qwen-Image-2512 generation (`src/generator.py`) — diffusers pipeline with BnB 4-bit CPU offload (works on RTX 4070 Ti 12GB), also ComfyUI path with GGUF workflow
- Model downloader (`src/downloader.py`) — from HuggingFace with retry logic
- One-click setup (`setup.bat`) — Miniconda env, all packages, ComfyUI cloned

**Tests:**
- `test_api.py` — 17/17 E2E API tests passed (submit→split→claim→upload→complete)
- `test_e2e_real.py` — Full pipeline with REAL Qwen AI on Layer 4, passed
- `test_timing.py` — Progress bar benchmark with test-shot timing estimation, working
- `test_layer1.py`, `test_real_layer.py`, `test_scale.py`, `test_step_by_step.py`, `test_one.py` — various generation/quality tests

**Hardware:** RTX 4070 Ti 12GB — Qwen 4-bit generation works (~3 min per layer at 512×384 / 15 steps)

**Recent work direction (last session, interrupted by Ctrl+C):**
- Testing individual layer generation quality (Layer 1 foreground, Layer 4 mid-distance)
- Object scaling for depth illusion (100% near → 70% far)
- Realistic D&D scene generation with distance-based prompt engineering

**Key decisions made:**
- All communication is polling-based via Flask (no WebSockets) — simpler, works over LAN/internet
- Workers generate independently, 6 separate Qwen runs (no cross-layer coordination)
- No cloud AI ever — local Qwen for both text splitting and image generation
- MySQL switch is a one-line config change (SQLAlchemy abstraction)
- ComfyUI bundled in repo for accessibility, but diffusers is default path
