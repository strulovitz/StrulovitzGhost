# 📊 StrulovitzGhost — Current Status (May 2026)

## 1. 🦖 Qwen-Image-Layered Research

**What:** Alibaba's model that natively outputs RGBA layers with transparency — no post-processing needed.

**Goal:** Replace the current Qwen-Image-2512 + green-screen/chroma-key pipeline with a model that outputs transparent layers directly.

**Key capabilities:**
- Decomposes any image into independent RGBA layers (foreground, midground, background)
- Preserves original art style, brushstrokes, and textures
- Inpaints hidden/occluded areas in the original style (genuine reconstruction, not cutouts)
- Trained on real Photoshop PSD documents
- Variable layer count (3-8 layers), recursive decomposition supported

**Hardware:**
- Full model: ~24-35GB VRAM → Laptop RTX 5090 24GB (tight, needs bf16 or FP8)
- Desktop RTX 4070 Ti 12GB: INT4 quantization, 512x512, 2-3 layers per pass
- Platforms: Diffusers or ComfyUI only (NOT Ollama)

**Status:** 🔬 RESEARCH PHASE — knowledge collected (Google AI deep dives in MEMORY.md Appendix A/B/C), zero code written, zero models downloaded.

---

## 2. 👻 V2 Pepper's Ghost Layers

**What:** Nir built a physical Pepper's Ghost rig with 6 semi-transparent plastic layers at different depths. V2 principles derived from real-world testing.

**10 V2 Principles (from Nir's physical testing):**
1. NO backgrounds — only objects (backgrounds seen through closer layers destroy the illusion)
2. Empty center every layer — transparent space in middle so deeper layers are visible
3. Characters must be bright — semi-transparent plastic dims everything
4. Far apart → close together with depth
5. Scaling: -15% per layer (L1=100%, L6=25%)
6. Vertical staggering — deeper = higher on canvas (Nir looks from above)
7. NO full-height objects (trees from top to bottom seen through characters)
8. NO ground — destroys illusion when seen through closer characters
9. Physical setup: 6 layers, 3 monitors, Nir looks from slightly above
10. Per-layer V2 spec written for all 6 layers:

| Layer | Content | Scale | Distance |
|-------|---------|-------|----------|
| 1 🦉 | Rabbit + root at bottom (no owl, no branches) | 100% | 20 cm |
| 2 🧝 | Elf + Human girls on log, gossiping, far apart | 85% | ~3 m |
| 3 🔥 | Dwarf + Halfling arguing (no fire or very dim) | 70% | ~10 m |
| 4 🐉 | Tiefling + Dragonborn sitting on rocks, together | 55% | ~20 m |
| 5 🌳 | Few trees, upper half only, self-contained, not bright | N/A | Far |
| 6 🌙 | Moon + stars only (no mountains) | 25% | Sky |

**How to generate:** Same pipeline as V1 (Qwen-Image-2512, 768×576, 15 steps) but with the V2 prompts above instead of the old prompts. Change from chroma-key green screen to rembg-based background removal (since characters can't have green screens — they need transparent backgrounds).

**Current layers:** Generated with V1 green-screen pipeline (old prompts). Should be replaced.

**Status:** 📋 SPEC COMPLETE — ZERO V2 layers generated. Ready to go, blocked on nothing.

**Who should generate:** Laptop RTX 5090 — faster (~4-5 min/layer at full precision vs ~9 min on 4070Ti), more VRAM for better quality.

---

## 3. 🎨 Fine Art Decomposition

**What:** New feature mode. Take famous paintings (Van Gogh Starry Night, Monet Water Lilies, etc.) and decompose them into 6 depth layers with transparent backgrounds, preserving the original art style including brushstrokes, pointillism, impasto textures.

**Relies on:** Qwen-Image-Layered model (Item #1 above) — existing Qwen-Image-2512 cannot do this.

**How it works:**
- Feed a painting image into Qwen-Image-Layered
- Model automatically separates into depth layers (sky → mountains → village → trees → foreground)
- Each output layer is independent RGBA PNG
- Hidden/occluded areas are inpainted in the original art style
- Low CFG (2.0-4.0) to prevent hallucination
- Can do recursive decomposition if single-pass has issues

**Hardware requirements:**
- Laptop RTX 5090 24GB: INT8 or FP16, 1024×1024, up to 8 layers single pass
- Desktop RTX 4070 Ti 12GB: INT4, 512×512, 2-3 layers per pass

**Status:** 📋 PLANNED — spec written, model capabilities researched (MEMORY.md Appendix C), zero code.

---

## 📋 Full Task/Priority List

| # | Task | Priority | Status | Who |
|---|------|----------|--------|-----|
| 1 | Generate V2 Pepper's Ghost layers (6 layers) | 🔴 HIGH | Not started | Laptop (5090) |
| 2 | Download Qwen-Image-Layered model | 🟡 MEDIUM | Not started | Laptop (5090, more VRAM) |
| 3 | Fine Art Decomposition: build pipeline | 🟡 MEDIUM | Not started | Both |
| 4 | ComfyUI path end-to-end test | 🟢 LOW | Not tested | Desktop |
| 5 | Hierarchical architecture | 🟢 LOW | Spec only | Future |
