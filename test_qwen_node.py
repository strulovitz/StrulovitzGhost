"""Test Q10 fix: Swap generic CLIPTextEncode+ReferenceLatent for native TextEncodeQwenImageEditPlus.
The hypothesis: Qwen's native node preserves the image's conditioning better than generic nodes.
"""
import json, urllib.request, time, os
from PIL import Image

COMFY_URL = "http://127.0.0.1:8188"
OUT = "C:/Users/nir_s/StrulovitzGhost/src/output"
SRC = "C:/Users/nir_s/Downloads/1920px-Great_Wave_off_Kanagawa2.jpg"

# Resize
img = Image.open(SRC).convert("RGBA")
img.thumbnail((640, 640), Image.LANCZOS)
prep = os.path.join(OUT, "test_qwen_input.png")
img.save(prep, "PNG")
print(f"Resized: {img.size}")

# Upload
boundary = "----FormBoundary7MA4YWxkTrZu0gW"
with open(prep, "rb") as f:
    img_bytes = f.read()
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="image"; filename="test_input.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()
req = urllib.request.Request(f"{COMFY_URL}/upload/image", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
image_name = json.loads(urllib.request.urlopen(req).read())["name"]
print(f"Uploaded: {image_name}")

prompt_nodes = {
    "27": {"class_type": "LoadImage", "inputs": {"image": image_name}},
    "37": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_layered_bf16.safetensors", "weight_dtype": "default"}},
    "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image", "device": "default"}},
    "39": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_layered_vae.safetensors"}},

    # NEW: Native Qwen conditioning node instead of CLIPTextEncode + ReferenceLatent
    "10": {
        "class_type": "TextEncodeQwenImageEditPlus",
        "inputs": {
            "clip": ["38", 0],
            "prompt": "a very close small wave and a close fishing boat on the right with only half visible,\na lower wave that stretches across from left to right,\na fishing boat at medium distance on the left with only half visible,\nthe great wave very tall on the left side and a far away fishing boat on the right side,\nfar away Mount Fuji slightly to the right and downward from the center,\nbeige colored sky,",
            "vae": ["39", 0],
            "image1": ["27", 0],
        }
    },

    # Negative conditioning — keep simple CLIPTextEncode
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["38", 0]}},

    # Encode image for negative ReferenceLatent
    "71": {"class_type": "VAEEncode", "inputs": {"pixels": ["27", 0], "vae": ["39", 0]}},

    # ReferenceLatent for negative only
    "70": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["7", 0], "latent": ["71", 0]}},

    "78": {"class_type": "GetImageSize", "inputs": {"image": ["27", 0]}},
    "83": {"class_type": "EmptyQwenImageLayeredLatentImage", "inputs": {"width": ["78", 0], "height": ["78", 1], "layers": 6, "batch_size": 1}},
    "66": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["37", 0], "shift": 1.0}},
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "model": ["66", 0],
            "positive": ["10", 0],   # ← Native Qwen conditioning
            "negative": ["70", 0],   # ← Simple CLIPTextEncode + ReferenceLatent for negative
            "latent_image": ["83", 0],
            "seed": 42, "steps": 50, "cfg": 4.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
        }
    },
    "76": {"class_type": "LatentCutToBatch", "inputs": {"samples": ["3", 0], "dim": "t", "slice_size": 1}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["76", 0], "vae": ["39", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "test_qwen_node"}},
}

req = urllib.request.Request(f"{COMFY_URL}/prompt", data=json.dumps({"prompt": prompt_nodes}).encode())
pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
print(f"Job: {pid}, waiting...")

while True:
    time.sleep(2)
    resp = json.loads(urllib.request.urlopen(f"{COMFY_URL}/history/{pid}").read())
    if pid in resp:
        s = resp[pid]
        if s["status"]["status_str"] == "error":
            print("ERROR:", s["status"]["messages"][-1])
            break
        outs = s.get("outputs", {})
        if outs:
            for nid, nout in outs.items():
                for im in nout.get("images", []):
                    src_url = f'{COMFY_URL}/view?filename={im["filename"]}&subfolder={im.get("subfolder","")}&type=output'
                    dst = os.path.join(OUT, im["filename"])
                    urllib.request.urlretrieve(src_url, dst)
                    print(f"  Saved: {dst}")
            break
print("DONE")
