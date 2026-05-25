"""ITG Splitter — Qwen-Image-Layered via ComfyUI.

Splits one RGBA image into 2 layers using ComfyUI's async weight offloading.
Reuses the node structure from run_comfy_decomp.py (proven working May 21).
"""

import os, sys, json, time, uuid, random, urllib.request
from PIL import Image
from io import BytesIO


COMFYUI_PORT = 8188

# Model files (must be in ComfyUI/models/ directories)
UNET_NAME = "qwen_image_layered_bf16.safetensors"
CLIP_NAME = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE_NAME = "qwen_image_layered_vae.safetensors"


def _comfy_url(host="127.0.0.1", port=None):
    p = port or COMFYUI_PORT
    return f"http://{host}:{p}"


def _comfy_upload(image_path, host="127.0.0.1", port=None):
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{os.path.basename(image_path)}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{_comfy_url(host, port)}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["name"]


def _comfy_submit(workflow, host="127.0.0.1", port=None):
    payload = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"{_comfy_url(host, port)}/prompt", data=payload)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["prompt_id"]


def _comfy_wait(prompt_id, output_dir, host="127.0.0.1", port=None, prefix="itg_split", timeout=600):
    url = _comfy_url(host, port)
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        resp = json.loads(urllib.request.urlopen(f"{url}/history/{prompt_id}", timeout=10).read())
        if prompt_id in resp:
            status = resp[prompt_id]
            if status["status"]["status_str"] == "error":
                raise RuntimeError(f"ComfyUI error: {status['status'].get('messages', ['unknown'])[-1]}")
            outputs = status.get("outputs", {})
            if outputs:
                saved = []
                for node_id, node_output in outputs.items():
                    for img in node_output.get("images", []):
                        src_url = f"{url}/view?filename={img['filename']}&subfolder={img.get('subfolder', '')}&type=output"
                        dst = os.path.join(output_dir, img["filename"])
                        urllib.request.urlretrieve(src_url, dst)
                        saved.append(dst)
                return saved
        print(f"  ComfyUI generating... ({int(time.time() - start)}s)", flush=True)

    raise TimeoutError(f"ComfyUI did not finish within {timeout}s")


def split_image_into_n_layers(image_path, output_dir, n=2, steps=20, cfg=4.0,
                               seed=None, prompt="", comfyui_host=None,
                               comfyui_port=None, unet_name=None, clip_name=None,
                               vae_name=None):
    """
    Split one RGBA image into N layers using Qwen-Image-Layered via ComfyUI.

    Args:
        image_path: Path to input RGBA PNG
        output_dir: Where to save output PNGs
        n: Number of layers (usually 2, max 8)
        steps: Sampling steps (20 recommended)
        cfg: CFG guidance scale (4.0 recommended)
        seed: Random seed (auto-generated if None)
        prompt: Decomposition prompt (empty = autonomous)
        comfyui_host: ComfyUI server host (default "127.0.0.1")
        comfyui_port: ComfyUI server port (default 8188)
        unet_name, clip_name, vae_name: Override model filenames

    Returns:
        List of paths to output RGBA PNG files (N layer files, excluding composite)
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    os.makedirs(output_dir, exist_ok=True)
    host = comfyui_host or "127.0.0.1"
    port = comfyui_port or COMFYUI_PORT

    # Prepare input: pad to 640x640 square
    img = Image.open(image_path).convert("RGBA")
    img.thumbnail((640, 640), Image.LANCZOS)
    square = Image.new("RGBA", (640, 640), (0, 0, 0, 0))
    offset_x = (640 - img.width) // 2
    offset_y = (640 - img.height) // 2
    square.paste(img, (offset_x, offset_y))

    prep_path = os.path.join(output_dir, f"split_input_{uuid.uuid4().hex[:6]}.png")
    square.save(prep_path, "PNG")
    print(f"  Prepared: {img.size} -> 640x640 padded", flush=True)

    # Upload to ComfyUI
    image_name = _comfy_upload(prep_path, host, port)

    # Build workflow
    workflow = {
        "27": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "37": {"class_type": "UNETLoader", "inputs": {"unet_name": unet_name or UNET_NAME, "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip_name or CLIP_NAME, "type": "qwen_image", "device": "default"}},
        "39": {"class_type": "VAELoader", "inputs": {"vae_name": vae_name or VAE_NAME}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["38", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["38", 0]}},
        "78": {"class_type": "GetImageSize", "inputs": {"image": ["27", 0]}},
        "83": {"class_type": "EmptyQwenImageLayeredLatentImage", "inputs": {"width": ["78", 0], "height": ["78", 1], "layers": n, "batch_size": 1}},
        "71": {"class_type": "VAEEncode", "inputs": {"pixels": ["27", 0], "vae": ["39", 0]}},
        "69": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["6", 0], "latent": ["71", 0]}},
        "70": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["7", 0], "latent": ["71", 0]}},
        "66": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["37", 0], "shift": 1.0}},
        "3": {"class_type": "KSampler", "inputs": {"model": ["66", 0], "positive": ["69", 0], "negative": ["70", 0], "latent_image": ["83", 0], "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "76": {"class_type": "LatentCutToBatch", "inputs": {"samples": ["3", 0], "dim": "t", "slice_size": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["76", 0], "vae": ["39", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "itg_split"}},
    }

    print(f"  Submitting to ComfyUI ({host}:{port}, layers={n}, steps={steps}, cfg={cfg}, seed={seed})...", flush=True)
    prompt_id = _comfy_submit(workflow, host, port)
    print(f"  Job submitted: {prompt_id}", flush=True)

    all_files = _comfy_wait(prompt_id, output_dir, host, port)
    print(f"  ComfyUI returned {len(all_files)} files", flush=True)

    # Filter: remove composite (file ending with _00001_ or the first one)
    layer_files = sorted([f for f in all_files if f.lower().endswith(".png")])
    if len(layer_files) > n:
        # Remove composite (usually the first file or the one with _00001_)
        layer_files = [f for f in layer_files if "_00001_" not in os.path.basename(f)][:n]

    # Clean up input temp
    try:
        os.remove(prep_path)
    except OSError:
        pass

    print(f"  Split complete: {len(layer_files)} layer files", flush=True)
    return layer_files
