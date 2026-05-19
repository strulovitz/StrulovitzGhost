import json
import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434/api/generate"
LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"

SPLIT_PROMPT_TEMPLATE = """You are a scene analyzer for a multi-layer Pepper's Ghost illusion system.
Break the following scene description into 6 depth layers, from farthest (layer 6) to closest (layer 1).

Layer 6 = furthest backdrop (night sky, moon, stars, light clouds — upper portion only, lower portion empty)
Layer 5 = far (a few individual trees, upper half only, self-contained, moonlit — no ground, no forest mass)
Layer 4 = mid-far (distant characters, sitting together, small scale ~55%, bright, no ground)
Layer 3 = mid (medium-distance characters, closer together than layer 2, small scale ~70%, bright, no ground)
Layer 2 = mid-close (closer characters, far apart from each other, scale ~85%, bright, no ground)
Layer 1 = closest (single nearest element at bottom edge, scale 100%, bright, no ground)

CRITICAL RULES for EVERY layer:
- Layers 1-5: NO backgrounds, NO ground, NO terrain — only isolated objects/characters
- Layer 6 EXCEPTION: upper half CAN be filled with night sky (stars, moon, clouds), lower half must be empty/transparent
- EMPTY CENTER in every layer — objects at edges, top, or bottom, never in the middle
- All characters must be BRIGHT and vivid
- Characters get CLOSER TOGETHER with depth (layer 2 far apart, layer 4 together)
- Deeper layers sit HIGHER on the canvas (vertical staggering)
- Use spatial composition: describe the empty space FIRST, then the objects
- Every object must be FULLY CONTAINED within the frame, not cut off
- Individual objects only — no mass of trees, no mass of clouds

For each layer, write a detailed image generation prompt following these rules.
Style: {style}
Scene: {scene}

Respond ONLY with valid JSON in this exact format:
{{
    "layers": [
        {{"layer": 6, "prompt": "..."}},
        {{"layer": 5, "prompt": "..."}},
        {{"layer": 4, "prompt": "..."}},
        {{"layer": 3, "prompt": "..."}},
        {{"layer": 2, "prompt": "..."}},
        {{"layer": 1, "prompt": "..."}}
    ]
}}"""


def split_scene_ollama(scene: str, style: str = "fantasy art", model: str = "qwen3") -> Optional[list]:
    prompt = SPLIT_PROMPT_TEMPLATE.format(style=style, scene=scene)
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "")
        return _parse_json_response(text)
    except Exception as e:
        print(f"Ollama error: {e}")
        return None


def split_scene_lmstudio(scene: str, style: str = "fantasy art", model: str = "auto") -> Optional[list]:
    prompt = SPLIT_PROMPT_TEMPLATE.format(style=style, scene=scene)
    try:
        response = requests.post(
            LMSTUDIO_URL,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return _parse_json_response(text)
    except Exception as e:
        print(f"LM Studio error: {e}")
        return None


def _parse_json_response(text: str) -> Optional[list]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        text = text.strip()
    try:
        result = json.loads(text)
        return result.get("layers", result if isinstance(result, list) else [])
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                return result.get("layers", [])
            except json.JSONDecodeError:
                pass
        return None


def split_scene(scene: str, style: str = "fantasy art", provider: str = "ollama", model: str = "qwen3") -> Optional[list]:
    if provider == "lmstudio":
        return split_scene_lmstudio(scene, style, model)
    return split_scene_ollama(scene, style, model)


def check_ollama_health() -> bool:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_lmstudio_health() -> bool:
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_llm_health(provider: str = "ollama") -> bool:
    if provider == "lmstudio":
        return check_lmstudio_health()
    return check_ollama_health()
