import json
import requests
from typing import Optional


OLLAMA_URL = "http://localhost:11434/api/generate"
LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"

SPLIT_PROMPT_TEMPLATE = """You are a scene analyzer for a 6-layer Pepper's Ghost display system.
Your job: take the user's input and produce 6 layers (layer 6=farthest to layer 1=closest), each with a positive prompt (what to draw) and a negative prompt (what to exclude).

--- STEP 1: DETECT THE INPUT FORMAT ---

The user's input could be one of two types:

TYPE A — Pre-structured layers: The input already has sections labeled "Layer 1", "Layer 2", etc., each with a "Prompt:" and "Negative prompt:" section. Some layers may also have "Prompt to copy/paste:" labels. The structure may be messy — there might be introductory paragraphs, "Important:" notes, style descriptions, etc.

TYPE B — Raw scene description: Just a paragraph or two describing a fantasy scene, with no per-layer breakdown.

--- STEP 2: PROCESS ACCORDINGLY ---

IMPORTANT: If the input starts with "[GLOBAL NEGATIVE PROMPT: ...]", those are global exclusions that must appear in EVERY layer's negative prompt. Combine them with the per-layer negatives.

If TYPE A (pre-structured layers):
- Find the positive prompt and negative prompt for each layer.
- CRITICAL: DO NOT SUMMARIZE, SHORTEN, OR REWRITE. Pass through the EXACT prompt text verbatim — every word of pose, clothing, position, color, lighting, art style, composition must be preserved. These are hand-crafted and must not be altered.
- Use the section labels ("Prompt:", "Prompt to copy/paste:", "Negative prompt:") to identify which text belongs where — put the text after "Prompt:" into the prompt field, and the text after "Negative prompt:" into the negative_prompt field.
- If a negative prompt says things like "no X, no Y" — convert to a clean comma-separated list: "X, Y"
- If a layer is completely missing, generate it from the other layers' context

If TYPE B (raw scene description):
- Analyze which objects/characters belong at which depth (farthest = background/sky/environment, closest = foreground framing)
- Generate both positive and negative prompts per layer following these rules:

Layer 6 = furthest backdrop (night sky, moon, stars, light clouds, mountains — upper portion only, lower empty)
Layer 5 = far (trees, forest, architecture — upper half only, no ground, no characters)
Layer 4 = mid-far (distant characters, together, scale ~55%, bright, no ground)
Layer 3 = mid (medium characters, closer than layer 4, scale ~70%, bright, no ground)
Layer 2 = mid-close (closer characters, far apart, scale ~85%, bright, no ground)
Layer 1 = closest (single element at bottom edge, scale 100%, bright, no ground)

V2 RULES for generated layers:
- Layers 1-5: NO backgrounds, NO ground, NO terrain — isolated objects/characters only
- Layer 6: ONLY layer with opaque backdrop (upper half); lower half empty/transparent
- EMPTY CENTER in every layer — objects at edges/top/bottom, never middle
- All characters BRIGHT and vivid
- Deeper layers sit HIGHER on canvas (vertical staggering)
- Every object FULLY CONTAINED within frame, not cut off
- Individual objects only — no mass of trees, no mass of clouds

NEGATIVE PROMPT RULES (both types):
- Layer 6: exclude ground, trees, characters, animals, objects, buildings
- Layer 5: exclude sky, moon, stars, characters, animals, ground
- Layers 4-1: exclude sky, moon, mountains, distant landscapes, elements from other layers
- Keep each negative prompt concise — combat the most likely hallucinations

--- OUTPUT FORMAT ---

Respond ONLY with valid JSON:
{{
    "layers": [
        {{"layer": 6, "prompt": "...", "negative_prompt": "..."}},
        {{"layer": 5, "prompt": "...", "negative_prompt": "..."}},
        {{"layer": 4, "prompt": "...", "negative_prompt": "..."}},
        {{"layer": 3, "prompt": "...", "negative_prompt": "..."}},
        {{"layer": 2, "prompt": "...", "negative_prompt": "..."}},
        {{"layer": 1, "prompt": "...", "negative_prompt": "..."}}
    ]
}}

Style: {style}
Scene: {scene}"""


def split_scene_ollama(scene: str, style: str = "Ghibli animation", model: str = "qwen3") -> Optional[list]:
    prompt = SPLIT_PROMPT_TEMPLATE.format(style=style, scene=scene)
    print(f"[LLM] Sending to {model} ({len(scene)} chars scene, {len(prompt)} chars template)...", flush=True)
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "")
        print(f"[LLM] Response: {len(text)} chars", flush=True)
        result = _parse_json_response(text)
        if result:
            for l in result:
                print(f"[LLM]   Layer {l['layer']}: prompt={len(l.get('prompt',''))}ch, neg={len(l.get('negative_prompt',''))}ch", flush=True)
        return result
    except Exception as e:
        print(f"[LLM] Ollama error: {e}", flush=True)
        return None


def split_scene_lmstudio(scene: str, style: str = "Ghibli animation", model: str = "auto") -> Optional[list]:
    prompt = SPLIT_PROMPT_TEMPLATE.format(style=style, scene=scene)
    print(f"[LLM] Sending to LM Studio ({len(scene)} chars scene)...", flush=True)
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
        print(f"[LLM] Response: {len(text)} chars", flush=True)
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


def split_scene(scene: str, style: str = "Ghibli animation", provider: str = "ollama", model: str = "qwen3") -> Optional[list]:
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
