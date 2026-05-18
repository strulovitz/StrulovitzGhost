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
) -> Optional[str]:
    try:
        from diffusers import DiffusionPipeline
        from downloader import check_model_cached, MODEL_DIFFUSERS_4BIT, MODEL_DIFFUSERS_FULL

        if check_model_cached(MODEL_DIFFUSERS_4BIT):
            model_id = MODEL_DIFFUSERS_4BIT
            print("Using 4-bit quantized model (fits 12GB VRAM)")
        elif check_model_cached(MODEL_DIFFUSERS_FULL):
            model_id = MODEL_DIFFUSERS_FULL
            print("Using full model (needs 20GB+ VRAM)")
        else:
            print("No model found! Please download a model first from the GUI.")
            return None

        print(f"Loading from: {model_id}")
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
        )

        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB VRAM)")

            if "bnb-4bit" in model_id or vram_gb < 16:
                print("Using CPU offload for memory efficiency...")
                pipe.enable_model_cpu_offload()
            else:
                pipe = pipe.to("cuda")
                print("Using CUDA directly")
        else:
            print("CUDA not available, using CPU (slow)")

        full_prompt = f"{prompt}, transparent background, isolated on transparent"

        print(f"Generating: {width}x{height}, {num_steps} steps...")
        image = pipe(
            prompt=full_prompt,
            negative_prompt="background, solid background, white background, black background, frame, border",
            width=width,
            height=height,
            num_inference_steps=num_steps,
            true_cfg_scale=guidance_scale,
        ).images[0]

        image.save(output_path)
        print(f"Saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"Diffusers generation error: {e}")
        import traceback
        traceback.print_exc()
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
) -> Optional[str]:
    if method == "comfyui":
        return generate_comfyui(prompt, output_path, width, height, num_steps, guidance_scale)
    return generate_diffusers(prompt, output_path, width, height, num_steps, guidance_scale)


if __name__ == "__main__":
    test_prompt = "A magical forest clearing at night with ancient oak trees, glowing fireflies, Ghibli animation style"
    test_output = os.path.join(os.path.dirname(__file__), "output", "test_generated.png")
    os.makedirs(os.path.dirname(test_output), exist_ok=True)
    result = generate_image(test_prompt, test_output, method="diffusers", width=512, height=384, num_steps=4)
    if result:
        print(f"Test successful! Image at: {result}")
    else:
        print("Test failed.")
