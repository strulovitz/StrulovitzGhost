"""
Submit Qwen-Image-Layered decomposition to running ComfyUI server.
Automatically resizes input image to 640px and converts to RGBA.
Usage: python run_comfy_decomp.py <path_to_painting.jpg>
"""
import json
import urllib.request
import time
import os
import sys
from PIL import Image

COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "C:/Users/nir_s/StrulovitzGhost/src/output"
STEPS = 8
CFG = 1.0
LAYERS = 6
SEED = 42
PREFIX = "great_wave_v2"  # Change this for each painting

# ----- Auto-resize input image -----
def prepare_image(input_path):
    """Resize any painting to 640px and convert to RGBA."""
    img = Image.open(input_path)
    img.thumbnail((640, 640), Image.LANCZOS)   # Preserve aspect ratio
    img = img.convert("RGBA")                   # Add alpha channel
    prepared_path = os.path.join(os.path.dirname(input_path), "prepared_input.png")
    img.save(prepared_path, "PNG")
    print(f"Resized: {img.size} -> {prepared_path}")
    return prepared_path

# Use command-line argument or default
if len(sys.argv) > 1:
    INPUT_IMAGE = sys.argv[1]
else:
    INPUT_IMAGE = "C:/Users/nir_s/StrulovitzGhost/src/output/starry_night_640.png"

# Always resize (idempotent — won't upscale if already smaller)
INPUT_IMAGE = prepare_image(INPUT_IMAGE)

# ----- Upload image via multipart -----
import io
boundary = "----FormBoundary7MA4YWxkTrZu0gW"
with open(INPUT_IMAGE, "rb") as f:
    img_bytes = f.read()

# Use unique filename based on painting name
import uuid
unique_name = f"{PREFIX}_{uuid.uuid4().hex[:6]}.png"

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="image"; filename="{unique_name}"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(
    f"{COMFY_URL}/upload/image",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)
resp = json.loads(urllib.request.urlopen(req).read())
image_name = resp["name"]   # Get the ACTUAL name ComfyUI assigned
print(f"Uploaded image: {image_name}")

# Build prompt using the blueprint's node structure
# Node IDs from the blueprint, with our overrides
prompt_nodes = {
    "27": {
        "class_type": "LoadImage",
        "inputs": {"image": image_name}
    },
    "37": {
        "class_type": "UNETLoader",
        "inputs": {"unet_name": "qwen_image_layered_bf16.safetensors", "weight_dtype": "default"}
    },
    "38": {
        "class_type": "CLIPLoader",
        "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image", "device": "default"}
    },
    "39": {
        "class_type": "VAELoader",
        "inputs": {"vae_name": "qwen_image_layered_vae.safetensors"}
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "Decompose this woodblock print into 6 depth layers from back to front: 1) sky and distant Mount Fuji, 2) far ocean horizon, 3) mid-distance waves, 4) the great wave crest with foam, 5) smaller foreground waves breaking, 6) closest wave spray and foam at the very front. Preserve the flat colors, clean edges, and woodblock print texture.", "clip": ["38", 0]}
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "", "clip": ["38", 0]}
    },
    "78": {
        "class_type": "GetImageSize",
        "inputs": {"image": ["27", 0]}
    },
    "83": {
        "class_type": "EmptyQwenImageLayeredLatentImage",
        "inputs": {"width": ["78", 0], "height": ["78", 1], "layers": LAYERS, "batch_size": 1}
    },
    "71": {
        "class_type": "VAEEncode",
        "inputs": {"pixels": ["27", 0], "vae": ["39", 0]}
    },
    "69": {
        "class_type": "ReferenceLatent",
        "inputs": {"conditioning": ["6", 0], "latent": ["71", 0]}
    },
    "70": {
        "class_type": "ReferenceLatent",
        "inputs": {"conditioning": ["7", 0], "latent": ["71", 0]}
    },
    "66": {
        "class_type": "ModelSamplingAuraFlow",
        "inputs": {"model": ["37", 0], "shift": 1.0}
    },
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "model": ["66", 0],
            "positive": ["69", 0],
            "negative": ["70", 0],
            "latent_image": ["83", 0],
            "seed": SEED,
            "steps": STEPS,
            "cfg": CFG,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0
        }
    },
    "76": {
        "class_type": "LatentCutToBatch",
        "inputs": {"samples": ["3", 0], "dim": "t", "slice_size": 1}
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["76", 0], "vae": ["39", 0]}
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {"images": ["8", 0], "filename_prefix": PREFIX}
    }
}

payload = json.dumps({"prompt": prompt_nodes}).encode()
print(f"Submitting job: {STEPS} steps, CFG {CFG}, {LAYERS} layers...")
req = urllib.request.Request(f"{COMFY_URL}/prompt", data=payload)
resp = json.loads(urllib.request.urlopen(req).read())
prompt_id = resp["prompt_id"]
print(f"Job submitted: {prompt_id}")

# Wait for completion
print("Waiting...")
while True:
    time.sleep(2)
    req = urllib.request.Request(f"{COMFY_URL}/history/{prompt_id}")
    resp = json.loads(urllib.request.urlopen(req).read())
    if prompt_id in resp:
        status = resp[prompt_id]
        if "outputs" in status:
            break
        # Check for errors
        if status.get("status", {}).get("status_str") == "error":
            print(f"ERROR: {status.get('status', {})}")
            raise SystemExit(1)

# Save outputs
print(f"Complete!")
for node_id, node_output in status["outputs"].items():
    for img_data in node_output.get("images", []):
        src_url = f"{COMFY_URL}/view?filename={img_data['filename']}&subfolder={img_data.get('subfolder', '')}&type=output"
        dst = os.path.join(OUTPUT_DIR, f"comfy_{img_data['filename']}")
        urllib.request.urlretrieve(src_url, dst)
        print(f"Saved: {dst}")

print("DONE")
