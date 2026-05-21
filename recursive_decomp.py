"""Recursive decomposition: 2 layers at a time, feed result back in."""
import json, urllib.request, time, os
from PIL import Image

COMFY_URL = "http://127.0.0.1:8188"
OUT = "C:/Users/nir_s/StrulovitzGhost/src/output"
SRC = "C:/Users/nir_s/Downloads/1920px-Great_Wave_off_Kanagawa2.jpg"

def decompose(img_path, prefix, prompt, layers=2):
    img = Image.open(img_path).convert("RGBA")
    img.thumbnail((512, 512), Image.LANCZOS)
    prep = os.path.join(OUT, f"{prefix}_input.png")
    img.save(prep, "PNG")
    print(f"Resized: {img.size}")

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    with open(prep, "rb") as f:
        img_bytes = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{prefix}.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    image_name = json.loads(urllib.request.urlopen(req).read())["name"]
    print(f"Uploaded: {image_name}")

    prompt_nodes = {
        "27": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "37": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_layered_bf16.safetensors", "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image", "device": "default"}},
        "39": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_layered_vae.safetensors"}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["38", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["38", 0]}},
        "78": {"class_type": "GetImageSize", "inputs": {"image": ["27", 0]}},
        "83": {"class_type": "EmptyQwenImageLayeredLatentImage", "inputs": {"width": ["78", 0], "height": ["78", 1], "layers": layers, "batch_size": 1}},
        "71": {"class_type": "VAEEncode", "inputs": {"pixels": ["27", 0], "vae": ["39", 0]}},
        "69": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["6", 0], "latent": ["71", 0]}},
        "70": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["7", 0], "latent": ["71", 0]}},
        "66": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["37", 0], "shift": 1.0}},
        "3": {"class_type": "KSampler", "inputs": {"model": ["66", 0], "positive": ["69", 0], "negative": ["70", 0], "latent_image": ["83", 0], "seed": 42, "steps": 50, "cfg": 4.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "76": {"class_type": "LatentCutToBatch", "inputs": {"samples": ["3", 0], "dim": "t", "slice_size": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["76", 0], "vae": ["39", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
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
                return []
            outs = s.get("outputs", {})
            if outs:
                saved = []
                for nid, nout in outs.items():
                    for im in nout.get("images", []):
                        src_url = f'{COMFY_URL}/view?filename={im["filename"]}&subfolder={im.get("subfolder","")}&type=output'
                        dst = os.path.join(OUT, im["filename"])
                        urllib.request.urlretrieve(src_url, dst)
                        saved.append(dst)
                        print(f"  Saved: {dst}")
                return saved

# STEP 1
print("=== STEP 1: layers=2, wave foreground ===")
step1 = decompose(SRC, "gw_s1", "the great wave with white foam crests in the foreground", layers=2)

# STEP 2: feed the 2nd file back (hopefully sky-removed)
if len(step1) >= 2:
    step2_input = step1[1]
    print(f"\n=== STEP 2: feeding {os.path.basename(step2_input)} back, sea horizon ===")
    step2 = decompose(step2_input, "gw_s2", "calm sea horizon and distant Mount Fuji", layers=2)

print("ALL DONE")
