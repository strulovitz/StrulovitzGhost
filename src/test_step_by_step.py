import sys, os, traceback
sys.path.insert(0, os.path.dirname(__file__))

print("Step 1: Import check...")
try:
    import torch
    from diffusers import DiffusionPipeline
    from PIL import Image
    print(f"   torch={torch.__version__}, CUDA={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   VRAM free: {torch.cuda.memory_allocated(0)/1e9:.1f} GB")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

print("Step 2: Load model...")
try:
    pipe = DiffusionPipeline.from_pretrained(
        "unsloth/Qwen-Image-2512-unsloth-bnb-4bit",
        torch_dtype=torch.bfloat16,
    )
    print("   Model loaded!")
except Exception as e:
    print(f"   FAIL: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Step 3: Enable CPU offload...")
try:
    pipe.enable_model_cpu_offload()
    print("   Offload enabled!")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

print("Step 4: Generate image (4 steps)...")
try:
    image = pipe(
        prompt="A cute small centered dragon, cartoon, on green screen background, isolated subject",
        negative_prompt="busy background, cluttered, close-up, multiple, frame filling",
        width=256,
        height=256,
        num_inference_steps=4,
        true_cfg_scale=4.0,
    ).images[0]
    print("   Image generated!")
except Exception as e:
    print(f"   FAIL: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Step 5: Remove background...")
try:
    from rembg import remove
    image = remove(image)
    print("   Background removed!")
except Exception as e:
    print(f"   FAIL: {e} (saving original)")
    traceback.print_exc()

out = os.path.join(os.path.dirname(__file__), "output", "test_step.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
image.save(out)
print(f"\nSUCCESS! Saved to {out}")
print(f"Image mode: {image.mode}, size: {image.size}")
