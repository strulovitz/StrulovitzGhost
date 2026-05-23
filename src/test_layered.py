"""Test Qwen-Image-Layered FP8 — decompose Starry Night into 6 RGBA layers."""
import os
import sys
import torch
from PIL import Image
from diffusers import QwenImageLayeredPipeline

# Input/output paths
INPUT_PATH = os.path.join(os.path.expanduser("~"), "Downloads",
    "1920px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "layered_test")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Input: {INPUT_PATH}")
print(f"Exists: {os.path.exists(INPUT_PATH)}")
print(f"VRAM free before load: {torch.cuda.mem_get_info()[0] / 1e9:.1f} GB")

print("\nLoading T5B/Qwen-Image-Layered-FP8...")
pipeline = QwenImageLayeredPipeline.from_pretrained(
    "T5B/Qwen-Image-Layered-FP8",
    local_files_only=True,
)
pipeline = pipeline.to("cuda")
pipeline.set_progress_bar_config(disable=None)

print(f"VRAM after load: {torch.cuda.mem_get_info()[0] / 1e9:.1f} GB free")
print(f"VRAM used: {torch.cuda.memory_allocated() / 1e9:.1f} GB")

# Load Starry Night
image = Image.open(INPUT_PATH).convert("RGBA")
print(f"Image size: {image.size}")

# Decompose into 6 layers
print("\nDecomposing into 6 layers...")
inputs = {
    "image": image,
    "generator": torch.Generator(device='cuda').manual_seed(42),
    "true_cfg_scale": 4.0,
    "negative_prompt": " ",
    "num_inference_steps": 50,
    "num_images_per_prompt": 1,
    "layers": 6,
    "resolution": 640,
    "cfg_normalize": True,
    "use_en_prompt": True,
}

with torch.inference_mode():
    output = pipeline(**inputs)
    output_images = output.images[0]

# Save layers
for i, layer_img in enumerate(output_images):
    path = os.path.join(OUTPUT_DIR, f"starry_night_layer_{i+1}.png")
    layer_img.save(path)
    print(f"  Layer {i+1}: {layer_img.size} -> {path}")

print(f"\nAll 6 layers saved to: {OUTPUT_DIR}")
