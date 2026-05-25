"""ITG Judge — Qwen3-VL quality gates + parent-anchored Z-ordering.

Uses Ollama's vision API: ollama.chat(model="qwen3-vl:4b", images=[...]).
"""

import os, sys, json, base64, time
import requests as http_requests

OLLAMA_URL = "http://localhost:11434/api/chat"


def _encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _ollama_chat(model, prompt, images_b64, timeout=300):
    """Call Ollama chat API. Default 300s timeout — first cold-load of 20GB vision models can take 2-3 minutes."""
    messages = [{"role": "user", "content": prompt, "images": images_b64}]
    resp = http_requests.post(OLLAMA_URL, json={"model": model, "messages": messages, "stream": False}, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama error: {resp.text}")
    return resp.json()["message"]["content"]


def _judge_with_retry(image_path, model, prompt, max_retries=3):
    """Call Qwen3-VL with retries. Cold-load of 20GB+ models can timeout on first attempt."""
    last_error = None
    for attempt in range(max_retries):
        try:
            img_b64 = _encode_image(image_path)
            response = _ollama_chat(model, prompt, [img_b64], timeout=120 + (attempt * 60))
            return json.loads(response.strip())
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                print(f"  Qwen3-VL attempt {attempt + 1} failed ({e}) — retrying...", flush=True)
                time.sleep(2)
    raise RuntimeError(f"Qwen3-VL failed after {max_retries} attempts: {last_error}")


def judge_layer_quality(image_path, model="qwen3-vl:4b", parent_description=""):
    """
    Ask Qwen3-VL: is this layer good or garbage?

    Returns: {"quality": "good"|"garbage", "description": "...", "confidence": 0.0-1.0}
    """
    img_b64 = _encode_image(image_path)

    prompt = f"""You are a quality control judge for an image decomposition pipeline.
{parent_description}

Look at this transparent image layer extracted from a larger artwork.

Answer these questions:
1. Is this image mostly a solid single color (all black, all white, all gray, or mostly transparent)?
2. Is this image blurry beyond recognition?
3. Does this image contain recognizable content (objects, shapes, textures, brushstrokes)?
4. Is this image worth keeping for a multi-layer Pepper's Ghost display?

Respond with ONLY this JSON:
{{"quality": "good" or "garbage", "description": "brief description of visible contents", "confidence": 0.0-1.0}}"""

    try:
        return _judge_with_retry(image_path, model, prompt)
    except Exception as e:
        print(f"  Qwen3-VL quality check FAILED after retries: {e}", flush=True)
        raise


def judge_layer_position(sub_part_path, parent_image_path, model="qwen3-vl:4b", parent_description=""):
    """
    Parent-anchored positioning: where is this sub-part in the WHOLE image?

    Returns: {"position": "front"|"middle"|"back", "description": "...", "hides": "..."}
    """
    sub_b64 = _encode_image(sub_part_path)
    parent_b64 = _encode_image(parent_image_path)

    prompt = f"""You see two images: the WHOLE image and ONE sub-part extracted from it.
{parent_description}

Describe the spatial position of the sub-part within the whole image.
Is it at the FRONT (closest to viewer/camera), MIDDLE, or BACK (farthest)?

Also note: does this sub-part visually OVERLAP or HIDE any other parts of the whole image?

Respond ONLY with JSON:
{{"position": "front" or "middle" or "back", "description": "brief spatial description of where this part is", "hides": "description of what it obscures, or 'nothing'"}}"""

    try:
        return _judge_with_retry(sub_part_path, model, prompt)
    except Exception as e:
        print(f"  Qwen3-VL position check FAILED after retries: {e}", flush=True)
        raise


def determine_z_order(sub_part_paths, parent_image_path, model="qwen3-vl:4b", parent_description=""):
    """
    Arrange N sub-parts by depth using parent-anchored positioning.

    Strategy:
    1. Compare EACH sub-part against the PARENT image (not against each other)
    2. From answers, infer Z-order (front=0, middle=1, back=2)
    3. Only ambiguous (same position) parts get occlusion check

    Returns: list of paths sorted closest (index 0) to farthest (index N-1).
    """
    if len(sub_part_paths) <= 1:
        return list(sub_part_paths)

    parent_b64 = _encode_image(parent_image_path)
    positions = {}

    for path in sub_part_paths:
        pos_info = judge_layer_position(path, parent_image_path, model, parent_description)
        positions[path] = pos_info
        time.sleep(0.3)  # Rate limit

    # Sort by position
    order = {"front": 0, "middle": 1, "back": 2}
    sorted_paths = sorted(sub_part_paths, key=lambda p: order.get(positions[p].get("position", "middle"), 1))

    # Resolve "middle" ambiguities with occlusion check
    middle_paths = [p for p in sorted_paths if positions[p].get("position") == "middle"]
    if len(middle_paths) > 1:
        middle_resolved = []
        for path in middle_paths:
            sub_b64 = _encode_image(path)
            prompt = """You see the WHOLE image and ONE sub-part.
Is this sub-part positioned IN FRONT OF other parts of the scene,
or BEHIND them, or NEITHER (same depth)?

Respond ONLY with: "front", "behind", or "neither"
"""
            try:
                answer = _ollama_chat(model, prompt, [parent_b64, sub_b64]).strip().lower()
            except Exception:
                answer = "neither"  # occlusion check is optional — "neither" is safe default
            middle_resolved.append((path, answer))
            time.sleep(0.3)

        # Reorder middle paths
        for path, rel in middle_resolved:
            idx = sorted_paths.index(path)
            if rel == "front":
                # Move to start of middle group
                sorted_paths.remove(path)
                mid_start = next((i for i, p in enumerate(sorted_paths) if positions[p].get("position") == "middle"), idx)
                sorted_paths.insert(mid_start, path)

    return sorted_paths
