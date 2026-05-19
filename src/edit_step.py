import torch, sys, time, traceback
from PIL import Image
from diffusers import QwenImageEditPlusPipeline

INPUT = "output/layer1_green.png"
OUTPUT = "output/layer1_clean.png"
STEPS = 10

try:
    print(f"[{time.strftime('%H:%M:%S')}] Loading edit model to GPU...", flush=True)
    pipe = QwenImageEditPlusPipeline.from_pretrained(
        "blanchon/Qwen-Image-Edit-2509-bnb-4bit",
        torch_dtype=torch.bfloat16
    ).to("cuda")
    print(f"[{time.strftime('%H:%M:%S')}] Model on GPU.", flush=True)

    image = Image.open(INPUT).convert("RGB")
    prompt = (
        "Remove any green color bleeding from the edges of the subjects. "
        "Clean up the green background so it is perfectly uniform #00FF00. "
        "Do not modify any subjects in any way — keep all details, textures, "
        "animals, branches, and ground completely unchanged."
    )

    print(f"[{time.strftime('%H:%M:%S')}] Starting edit ({STEPS} steps, ~{STEPS*95//60} min)...", flush=True)
    start = time.time()

    with torch.inference_mode():
        output = pipe(
            image=[image],
            prompt=prompt,
            true_cfg_scale=4.0,
            negative_prompt=" ",
            num_inference_steps=STEPS,
            guidance_scale=1.0,
            num_images_per_prompt=1,
        )

    elapsed = time.time() - start
    output.images[0].save(OUTPUT)
    print(f"[{time.strftime('%H:%M:%S')}] Saved: {OUTPUT} ({elapsed:.0f}s)", flush=True)

    del pipe
    torch.cuda.empty_cache()
    print(f"[{time.strftime('%H:%M:%S')}] Done.", flush=True)

except Exception as e:
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
