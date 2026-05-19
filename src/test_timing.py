import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 50)
print("  STRULOVITZ GHOST - TIMING BENCHMARK")
print("=" * 50)

import torch
from diffusers import DiffusionPipeline

print(f"\nGPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB\n")

print("[1/3] Loading model...")
t0 = time.time()
pipe = DiffusionPipeline.from_pretrained(
    "unsloth/Qwen-Image-2512-unsloth-bnb-4bit",
    torch_dtype=torch.bfloat16,
)
pipe.enable_model_cpu_offload()
print(f"      Loaded in {time.time() - t0:.1f}s\n")

step_times = []

def cb(pipeline, step, timestep, kwargs):
    now = time.time()
    if hasattr(cb, "last"):
        elapsed = now - cb.last
        step_times.append(elapsed)
        done = len(step_times)
        avg = sum(step_times) / done
        eta = avg * (total_steps - done)
        print(f"      Step {done}/{total_steps} | {elapsed:.1f}s this step | ~{eta:.0f}s remaining")
    cb.last = now
    return kwargs

print("[2/3] Quick test shot (4 steps, 128x128) for timing estimate...")
total_steps = 4
cb.last = time.time()
t0 = time.time()
image_small = pipe(
    prompt="A tiny cute dragon, cartoon, centered, green screen background, isolated subject",
    negative_prompt="busy background, cluttered, close-up, frame filling",
    width=128, height=128,
    num_inference_steps=total_steps,
    true_cfg_scale=4.0,
    callback_on_step_end=cb,
    callback_on_step_end_tensor_inputs=["latents"],
)
test_time = time.time() - t0
avg_step = sum(step_times) / len(step_times) if step_times else test_time / total_steps
print(f"      Total: {test_time:.1f}s | Avg per step: {avg_step:.1f}s\n")

step_times.clear()

print("[3/3] Full generation (15 steps, 512x384) with live progress...")
total_steps = 15
est_total = avg_step * total_steps
print(f"      Estimated total time: ~{est_total:.0f}s ({est_total/60:.1f} min)")
print()

cb.last = time.time()
t0 = time.time()
image = pipe(
    prompt="A cute small dragon, cartoon style, centered, on green screen, isolated subject, studio lighting",
    negative_prompt="busy background, cluttered, close-up, frame filling, multiple objects",
    width=512, height=384,
    num_inference_steps=total_steps,
    true_cfg_scale=4.0,
    callback_on_step_end=cb,
    callback_on_step_end_tensor_inputs=["latents"],
)
gen_time = time.time() - t0

out = os.path.join(os.path.dirname(__file__), "output", "test_timing_dragon.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
image.save(out)

print(f"\n{'=' * 50}")
print(f"  DONE!")
print(f"  Test shot (4 steps): {test_time:.0f}s")
print(f"  Full gen (15 steps): {gen_time:.0f}s")
print(f"  Accuracy: estimate was {est_total:.0f}s, actual was {gen_time:.0f}s")
print(f"  Saved: {out}")
print(f"{'=' * 50}")
