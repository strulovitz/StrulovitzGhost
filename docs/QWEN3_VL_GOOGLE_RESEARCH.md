# 🔬 Qwen3-VL Model Research — Google AI Search Answer (May 25, 2026)

**Question asked:**
> "What are the available versions and quantizations of Qwen3-VL in Ollama as of May 2026?"

**Answer (verbatim from Google AI):**

---

As of May 2026, Ollama officially supports the Qwen3-VL model family locally across five distinct sizes: 2B, 4B, 8B, 30B (MoE), and 32B (Dense). The default quantizations natively served by Ollama typically use standard 4-bit configurations (q4_K_M), but variants ranging up to 8-bit (q8_0) are widely available or easily packaged.

For your specific use case—judging transparent PNG layer artifacts (garbage vs. clear content) and calculating depth occlusion—the models display distinct trade-offs in VRAM footprint, vision reasoning, and processing speed.

## Hardware Allocation & Model Trade-offs

The spatial perception engine in Qwen3-VL includes an advanced 2D/3D coordinate system and enhanced occlusion reasoning. This makes the larger parameters significantly better at understanding overlapping layers than smaller parameters.

| Model Size | Quantization | Approx. VRAM (Model + Vision Tokens) | Laptop (RTX 5090 - 24GB) | Desktop (RTX 4070 Ti - 12GB) | Vision Task Suitability (Image Quality & Depth) | Speed |
|---|---|---|---|---|---|---|
| 4B / 8B | q4_K_M | ~4GB - 7GB | Runs flawlessly (Leaves headroom) | Recommended Local Choice (Fits comfortably) | Moderate: Great at basic quality checks (blurry vs. sharp); struggle with complex 3D depth occlusions. | Fast (~40+ tok/s) |
| 8B | q8_0 | ~10GB - 11GB | Runs flawlessly | Fits tight (Minimal context headroom) | Good: High visual fidelity preservation; fewer quantization artifacts on low-level pixels. | Moderate |
| 30B / 32B | q4_K_M | ~20GB - 22GB | Recommended Flagship Choice (Fits fully in VRAM) | Will spill to System RAM (Extremely slow) | Excellent: Strong advanced spatial perception, viewpoint calculations, and layout reasoning. | Slow to Moderate |

**Note:** Vision-Language Models (VLMs) consume variable VRAM based on image resolution. When Qwen3-VL breaks down images dynamically into visual tokens, a high-resolution canvas can add 2GB–4GB of overhead to the baseline VRAM figures listed above.

## Recommended Quantization for Your Use Case

For your hardware and image-analysis pipeline, the optimal choice depends on which machine you are operating:

### 1. Laptop (RTX 5090 24GB VRAM): Use `qwen3-vl:32b` or `qwen3-vl:30b` at 4-bit (q4_K_M)
- **Why:** Determining depth ordering of image layers is a highly abstract technical task. Qwen3-VL 30B/32B feature significantly upgraded spatial reasoning and occlusion capabilities compared to the 8B model.
- **The Fit:** A 4-bit quantization of the 30B/32B size takes up ~20GB of VRAM, sitting safely inside your 5090's 24GB allocation with room for processing visual tokens.

### 2. Desktop (RTX 4070 Ti 12GB VRAM): Use `qwen3-vl:8b` at 8-bit (q8_0)
- **Why:** Your task involves catching raw pixel degradation, such as "garbage" artifacts, solid color blocks, and slight blur on transparent layers. Low-bit quantizations (like 4-bit) can degrade texturing and noise profiles. An 8-bit model preserves the weights of the visual encoder much better, meaning fewer false positives on artifact detection.
- **The Fit:** The 8B model at q8_0 takes ~10GB, allowing it to remain entirely on your 12GB desktop card during execution.

## Prompting Tip for Transparent PNGs

Because local LLMs convert inputs to RGB arrays internally, alpha transparency can sometimes render as a stark solid black or white background. When asking the model to evaluate layers, explicitly prompt it:

> "Analyze this layer. Note that any solid background is a transparency mask. Determine if the foreground element contains recognizable high-quality visual content or if it consists of low-quality, blurry noise, or compression garbage."

---

## Decision for StrulovitzGhost ITG

| Machine | Model | VRAM | Role |
|---------|-------|------|------|
| Laptop (RTX 5090) | `qwen3-vl:32b` or `30b` (4-bit) | ~20-22 GB | Quality judge + Z-ordering (Boss + Worker) |
| Desktop (RTX 4070 Ti) | `qwen3-vl:8b` (8-bit q8_0) | ~10 GB | Quality judge (Worker only) |

**Note:** Desktop also needs ComfyUI for splitting — but ComfyUI uses the LAPTOP's instance over LAN (Desktop's 12GB can't fit the 40GB UNET). Desktop needs Ollama with qwen3-vl locally for quality judging since `itg_judge.py` hardcodes `localhost:11434`.

**Pull commands:**
```
# Laptop
ollama pull qwen3-vl:32b

# Desktop
ollama pull qwen3-vl:8b
```
