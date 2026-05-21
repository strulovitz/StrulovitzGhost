# Desktop Setup Guide — Qwen-Image-Layered via ComfyUI

**For:** Desktop Windows PC with RTX 4070 Ti 12 GB VRAM, 64 GB RAM
**Goal:** Decompose images into RGBA layers using Qwen-Image-Layered

---

## 1. Create Conda Environment

Open **Anaconda Prompt** (not PowerShell) and run:

```
conda create -n comfyui python=3.11 -y
conda activate comfyui
```

The desktop uses `torch 2.12.0+cu126` (Ada Lovelace architecture).
Do NOT use `torch 2.11.0+cu128` — that's for Blackwell (RTX 5090) only.

---

## 2. Install PyTorch

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

**Verify GPU works:**

```
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

Should print: `NVIDIA GeForce RTX 4070 Ti`
If it prints `CPU` or errors, the GPU driver or PyTorch version is wrong.

---

## 3. Install ComfyUI

```
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
```

This creates a `ComfyUI/` folder in your current directory. Note where you ran this.

---

## 4. Download the 3 Model Files

**Total download: ~50.5 GB.** Make sure you have enough disk space (60+ GB free).

Run these Python commands one at a time (in the comfyui conda env):

### File 1: UNET / Diffusion Model (40.9 GB)

```python
from huggingface_hub import hf_hub_download
hf_hub_download(
    "Comfy-Org/Qwen-Image-Layered_ComfyUI",
    "split_files/diffusion_models/qwen_image_layered_bf16.safetensors",
    local_dir=".",
    local_dir_use_symlinks=False
)
```

After download, the file is at: `./split_files/diffusion_models/qwen_image_layered_bf16.safetensors`

**Copy it to ComfyUI:**

```
copy "split_files\diffusion_models\qwen_image_layered_bf16.safetensors" "ComfyUI\models\diffusion_models\"
```

### File 2: CLIP / Text Encoder (9.4 GB)

```python
from huggingface_hub import hf_hub_download
hf_hub_download(
    "f5aiteam/CLIP",
    "qwen_2.5_vl_7b_fp8_scaled.safetensors",
    local_dir=".",
    local_dir_use_symlinks=False
)
```

**Copy to ComfyUI:**

```
copy "qwen_2.5_vl_7b_fp8_scaled.safetensors" "ComfyUI\models\text_encoders\"
```

### File 3: VAE (0.25 GB)

```python
from huggingface_hub import hf_hub_download
hf_hub_download(
    "Comfy-Org/Qwen-Image-Layered_ComfyUI",
    "split_files/vae/qwen_image_layered_vae.safetensors",
    local_dir=".",
    local_dir_use_symlinks=False
)
```

**Copy to ComfyUI:**

```
copy "split_files\vae\qwen_image_layered_vae.safetensors" "ComfyUI\models\vae\"
```

### Verify All 3 Files Are in Place

```
dir ComfyUI\models\diffusion_models\qwen_image_layered_bf16.safetensors
dir ComfyUI\models\text_encoders\qwen_2.5_vl_7b_fp8_scaled.safetensors
dir ComfyUI\models\vae\qwen_image_layered_vae.safetensors
```

All three should show file sizes.

---

## 5. Get the Runner Script

The decomposition script is in the StrulovitzGhost GitHub repo:

```
git clone https://github.com/strulovitz/StrulovitzGhost.git
```

The file you need is: `StrulovitzGhost/run_comfy_decomp.py`

Open it in a text editor and change these lines at the top to match your paths:

```python
COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "C:/path/to/your/output/folder"    # Change this!
STEPS = 50
CFG = 4.0
LAYERS = 4         # Start with 4. Can try 6 or 8 for more separation.
SEED = 42
SHIFT = 1.0
PREFIX = "my_image"   # Change for each painting
```

The script automatically resizes images to 640px. No manual resizing needed.

---

## 6. Start ComfyUI

In the comfyui conda env, from the ComfyUI folder:

```
python main.py --port 8188
```

Wait for this line:
```
Total VRAM XXXX MB, total RAM 64957 MB
Set vram state to: NORMAL_VRAM
Device: cuda:0 NVIDIA GeForce RTX 4070 Ti
```

If you see "To see the GUI go to: http://127.0.0.1:8188" — it's ready.

---

## 7. Run a Decomposition

In a **second terminal** (keep ComfyUI running in the first one):

```
conda activate comfyui
python StrulovitzGhost/run_comfy_decomp.py "C:\path\to\your\image.jpg"
```

Wait. The script prints progress. When done, it saves 5 files:
- `comfy_<prefix>_00001_.png` — original composite
- `comfy_<prefix>_00002_.png` through `_00005_.png` — 4 decomposition layers

---

## 8. What Settings We KNOW Work

Based on laptop testing (May 21, 2026):

| Parameter | Value | Notes |
|-----------|-------|-------|
| Steps | 50 | Good balance of quality vs speed |
| CFG | 4.0 | Lower (1.0) = worse, higher (8+) = burns |
| Layers | 4 | Start here, try 6 or 8 for more separation |
| Resolution | 640px | Auto-resized by script |
| Prompt | Empty ("") | Works BETTER without prompts for most images |
| Negative prompt | Empty ("") | Always leave blank |
| Seed | 42 | Fixed for reproducibility |
| VAE | qwen_image_layered_vae.safetensors | CRITICAL — standard VAEs don't work |
| CLIP type | qwen_image | Must be set in CLIPLoader node |

---

## 9. What We LEARNED (So You Don't Waste Time)

1. **Photographs work best.** The model was trained on Photoshop PSDs — photos with clear subjects against backgrounds decompose well.

2. **Comics work OK.** Hard lines, flat colors — similar to graphic design.

3. **Paintings rarely work.** Monet, Van Gogh, Hokusai — impressionist brushwork confuses the model. Renaissance paintings (Mona Lisa) also failed.

4. **CPU offloading is REQUIRED.** The BF16 model is ~40 GB. Your 12 GB VRAM cannot hold it. ComfyUI handles offloading automatically — you don't need to configure anything.

5. **The LAST output layer is often the best one.** Layer 00005 (or the highest number) consistently shows the best separation. Earlier layers may be duplicates or black.

6. **If it works, you can recurse.** Take a good output layer, feed it back into the pipeline, and decompose it further.

7. **No prompt = often better than wrong prompt.** The model decides autonomously based on depth and occlusion. A wrong prompt can make things worse.

---

## 10. If You Get OOM (Out of Memory)

- Lower steps to 20
- Make sure no other GPU apps are running
- Restart ComfyUI (clears VRAM)
- The laptop used 640px without OOM on 24 GB. On 12 GB, the same settings should work but will be slower due to more aggressive offloading.

---

## 11. Speed Expectations

| | Laptop (RTX 5090 24GB) | Desktop (RTX 4070 Ti 12GB) |
|---|---|---|
| Per run (50 steps, 4 layers) | ~2-3 min | ~8-12 min (estimated) |
| First run after startup | ~3-5 min | ~15-20 min |

The desktop is 3-4x slower because the smaller VRAM means more CPU↔GPU transfers per step. The model is the same, the quality is the same — only the speed differs.
