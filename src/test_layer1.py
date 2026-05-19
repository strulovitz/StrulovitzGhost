import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 50)
print("  STRULOVITZ GHOST - LAYER 1 (Closest)")
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

print("[2/3] Quick test shot (4 steps, 128x128) for timing...")
total_steps = 4
cb.last = time.time()
t0 = time.time()
image_small = pipe(
    prompt="test shot tiny",
    negative_prompt="",
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
print(f"      Estimated total: ~{est_total:.0f}s ({est_total/60:.1f} min)\n")

PROMPT = (
    "Ghibli animation style. "
    "Tree branch tips entering from the left and right edges, framing the scene like a window. "
    "On one branch, an owl sits silently, watching. "
    "On the ground at the bottom, a thick tree root with detailed bark texture, "
    "drawn as if viewed from very close, 20 centimeters away — large, textured, immersive. "
    "A curious rabbit sits on the root, its back turned to the viewer, looking forward. "
    "The ground is drawn from extremely close — detailed moss, grass blades, and textures. "
    "Green screen background in the center where the clearing view would be. "
    "Clean edges. Isolated subjects."
)

cb.last = time.time()
t0 = time.time()
result = pipe(
    prompt=PROMPT,
    negative_prompt="busy background, cluttered, close-up, frame filling, multiple objects, text, watermark",
    width=512, height=384,
    num_inference_steps=total_steps,
    true_cfg_scale=4.0,
    callback_on_step_end=cb,
    callback_on_step_end_tensor_inputs=["latents"],
)
gen_time = time.time() - t0
image = result.images[0]

out = os.path.join(os.path.dirname(__file__), "output", "layer1_foreground.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
image.save(out)

print(f"\n{'=' * 50}")
print(f"  LAYER 1 DONE!")
print(f"  Test shot: {test_time:.0f}s | Full gen: {gen_time:.0f}s")
print(f"  Saved: {out}")
print(f"{'=' * 50}")
