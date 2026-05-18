import json
import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434/api/generate"
LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"

SPLIT_PROMPT_TEMPLATE = """You are a scene analyzer for a multi-layer image generation system.
Break the following scene description into 6 depth layers, from farthest (layer 6) to closest (layer 1).

Layer 6 = farthest background (sky, moon, stars, far mountains)
Layer 5 = far background (forest, distant buildings, horizon)
Layer 4 = mid-far (structures, trees, distant characters)
Layer 3 = mid (medium-distance characters and objects)
Layer 2 = mid-close (closer characters, campfire, foreground details)
Layer 1 = closest (very near elements, framing branches, nearest characters)

For each layer, write a detailed image generation prompt that describes ONLY what appears in that layer.
Everything else in that layer should be transparent — mention this explicitly.
Each prompt must include the description of the elements, their position, lighting, and mood.

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
