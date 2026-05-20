import sys, os, traceback
sys.path.insert(0, os.path.dirname(__file__))

import torch
from diffusers import DiffusionPipeline

try:
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    print("Loading Qwen-Image-2512 with CPU offload (for 12GB GPUs)...")
    pipe = DiffusionPipeline.from_pretrained(
        "Qwen/Qwen-Image-2512",
        torch_dtype=torch.bfloat16,
    )

    print("Enabling sequential CPU offload...")
    pipe.enable_sequential_cpu_offload()

    print("Generating test image (256x256, 4 steps)...")
    image = pipe(
        prompt="A cute dragon, cartoon style, transparent background",
        negative_prompt="background, solid background",
        width=256,
        height=256,
        num_inference_steps=4,
        guidance_scale=4.0,
    ).images[0]

    out = os.path.join(os.path.dirname(__file__), "output", "test_qwen_4bit.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    image.save(out)
    print(f"SUCCESS! Saved to {out}")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
