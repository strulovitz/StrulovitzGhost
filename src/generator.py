import os
import sys
import json
import time
import subprocess
import requests
from typing import Optional

import torch
from PIL import Image


MODEL_DIFFUSERS_4BIT = "unsloth/Qwen-Image-2512-unsloth-bnb-4bit"
MODEL_DIFFUSERS_FULL = "Qwen/Qwen-Image-2512"
COMFYUI_DIR = os.path.join(os.path.dirname(__file__), "comfyui")
COMFYUI_PORT = 8188
COMFYUI_URL = f"http://localhost:{COMFYUI_PORT}"


def generate_diffusers(
    prompt: str,
    output_path: str,
    width: int = 1024,
    height: int = 768,
    num_steps: int = 28,
    guidance_scale: float = 4.0,
    remove_bg: bool = True,
    progress_callback=None,
) -> Optional[str]:
    try:
        from diffusers import DiffusionPipeline
        from downloader import check_model_cached, MODEL_DIFFUSERS_4BIT, MODEL_DIFFUSERS_FULL

        if check_model_cached(MODEL_DIFFUSERS_4BIT):
            model_id = MODEL_DIFFUSERS_4BIT
        elif check_model_cached(MODEL_DIFFUSERS_FULL):
            model_id = MODEL_DIFFUSERS_FULL
        else:
            print("No model found! Please download a model first from the GUI.")
            return None

        if progress_callback:
            progress_callback("Loading model...", 3)

        pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16)

        if torch.cuda.is_available() and ("bnb-4bit" in model_id or torch.cuda.get_device_properties(0).total_memory < 16e9):
            pipe.enable_model_cpu_offload()
        elif torch.cuda.is_available():
            pipe = pipe.to("cuda")

        if progress_callback:
            progress_callback("Running timing test shot...", 8)

        step_times = []

        def timing_cb(pipeline, step, timestep, kwargs):
            now = time.time()
            if hasattr(timing_cb, "last"):
                step_times.append(now - timing_cb.last)
            timing_cb.last = now
            return kwargs

        timing_cb.last = time.time()
        pipe(
            prompt="test shot",
            negative_prompt="",
            width=64, height=64,
            num_inference_steps=3,
            true_cfg_scale=4.0,
            callback_on_step_end=timing_cb,
            callback_on_step_end_tensor_inputs=["latents"],
        )

        sec_per_step = sum(step_times) / len(step_times) if step_times else 18.0
        pixels = width * height
        test_pixels = 64 * 64
        est_sec_per_step = sec_per_step * (pixels / test_pixels) * 0.6
        est_total = est_sec_per_step * num_steps

        if progress_callback:
            progress_callback(
                f"Estimated: ~{est_total/60:.1f} min ({num_steps} steps, {width}x{height})",
                10,
            )

        full_prompt = (
            f"{prompt}. The subject is small and centered on a plain green screen background. "
            f"Isolated subject. Studio lighting. Clean edges."
        )

        class ProgressTracker:
            def __init__(self):
                self.start_time = time.time()
                self.step_times = []

            def __call__(self, pipeline, step_idx, timestep, callback_kwargs):
                now = time.time()
                if self.step_times:
                    self.step_times.append(now - self._last)
                self._last = now
                if progress_callback and self.step_times:
                    done = len(self.step_times)
                    avg = sum(self.step_times) / done
                    remaining = (num_steps - done) * avg
                    pct = 10 + int(80 * done / num_steps)
                    progress_callback(
                        f"Step {done}/{num_steps} | ~{remaining:.0f}s left", pct
                    )
                return callback_kwargs

            def get_total(self):
                return time.time() - self.start_time

        tracker = ProgressTracker()
        tracker._last = time.time()
        tracker.start_time = time.time()

        result = pipe(
            prompt=full_prompt,
            negative_prompt="busy background, cluttered, multiple objects, frame filling, close-up, border, text, watermark",
            width=width,
            height=height,
            num_inference_steps=num_steps,
            true_cfg_scale=guidance_scale,
            callback_on_step_end=tracker,
            callback_on_step_end_tensor_inputs=["latents"],
        )
        image = result.images[0]

        if remove_bg:
            if progress_callback:
                progress_callback("Removing background...", 92)
            try:
                from rembg import remove
                image = remove(image)
            except Exception as e:
                print(f"Background removal failed: {e}")

        image.save(output_path)
        gen_time = tracker.get_total()
        if progress_callback:
            progress_callback(f"Done in {gen_time:.0f}s!", 100)
        print(f"Generated in {gen_time:.0f}s, saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"Generation error: {e}")
        import traceback
        traceback.print_exc()
        if progress_callback:
            progress_callback(f"Error: {e}", -1)
        return None


def _start_comfyui() -> bool:
    if _is_comfyui_running():
        return True

    comfy_main = os.path.join(COMFYUI_DIR, "main.py")
    if not os.path.exists(comfy_main):
        print("ComfyUI not found. Please run setup first.")
        return False

    print("Starting ComfyUI server...")
    subprocess.Popen(
        [sys.executable, comfy_main, "--port", str(COMFYUI_PORT)],
        cwd=COMFYUI_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(60):
        time.sleep(2)
        if _is_comfyui_running():
            print("ComfyUI server ready!")
            return True
        print("Waiting for ComfyUI...")

    print("ComfyUI failed to start.")
    return False


def _is_comfyui_running() -> bool:
    try:
        r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def generate_comfyui(
    prompt: str,
    output_path: str,
    width: int = 1024,
    height: int = 768,
    num_steps: int = 28,
    guidance_scale: float = 4.0,
    seed: int = 42,
) -> Optional[str]:
    try:
        if not _start_comfyui():
            return None

        workflow = _build_qwen_workflow(prompt, width, height, num_steps, guidance_scale, seed)

        print("Submitting workflow to ComfyUI...")
        r = requests.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow},
            timeout=10,
        )
        if r.status_code != 200:
            print(f"ComfyUI prompt error: {r.text}")
            return None

        prompt_id = r.json().get("prompt_id")
        print(f"Prompt ID: {prompt_id}")

        for _ in range(300):
            time.sleep(2)
            r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10)
            if r.status_code != 200:
                continue
            history = r.json()
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_id, node_output in outputs.items():
                    images = node_output.get("images", [])
                    if images:
                        img_data = images[0]
                        filename = img_data["filename"]
                        img_url = f"{COMFYUI_URL}/view?filename={filename}&type=output"
                        img_response = requests.get(img_url, timeout=30)
                        if img_response.status_code == 200:
                            img = Image.open(requests.compat.BytesIO(img_response.content))
                            img.save(output_path)
                            print(f"Saved: {output_path}")
                            return output_path
                print("Generation complete but no image found.")
                return None
            print("Generating...")

        print("Timed out waiting for ComfyUI.")
        return None

    except Exception as e:
        print(f"ComfyUI generation error: {e}")
        return None


def _build_qwen_workflow(
    prompt: str,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    seed: int,
) -> dict:

    full_prompt = f"{prompt}, transparent background, isolated subject on transparent"
    negative = "background, solid background, white background, black background"

    return {
        "3": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "4": {
            "inputs": {"ckpt_name": "qwen_image_2512.safetensors"},
            "class_type": "CheckpointLoaderSimple",
        },
        "5": {
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "class_type": "EmptyLatentImage",
        },
        "6": {
            "inputs": {"text": full_prompt, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {"text": negative, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "8": {
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            "class_type": "VAEDecode",
        },
        "9": {
            "inputs": {"filename_prefix": "strulovitz", "images": ["8", 0]},
            "class_type": "SaveImage",
        },
    }


def generate_image(
    prompt: str,
    output_path: str,
    method: str = "diffusers",
    width: int = 1024,
    height: int = 768,
    num_steps: int = 28,
    guidance_scale: float = 4.0,
    remove_bg: bool = True,
    progress_callback=None,
) -> Optional[str]:
    if method == "comfyui":
        return generate_comfyui(prompt, output_path, width, height, num_steps, guidance_scale)
    return generate_diffusers(
        prompt, output_path, width, height, num_steps,
        guidance_scale, remove_bg, progress_callback,
    )


if __name__ == "__main__":
    test_prompt = "A magical forest clearing at night with ancient oak trees, glowing fireflies, Ghibli animation style"
    test_output = os.path.join(os.path.dirname(__file__), "output", "test_generated.png")
    os.makedirs(os.path.dirname(test_output), exist_ok=True)
    result = generate_image(test_prompt, test_output, method="diffusers", width=512, height=384, num_steps=4)
    if result:
        print(f"Test successful! Image at: {result}")
    else:
        print("Test failed.")
