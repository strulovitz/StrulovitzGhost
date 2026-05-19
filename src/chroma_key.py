"""Chroma-key any solid screen color to transparent alpha.
Usage: python chroma_key.py <input> <output> [color]
  color: 'green' (default), 'red', or 'blue'
"""
import sys
from PIL import Image
import numpy as np

# Color definitions: RGB values for each key color
COLORS = {
    "green": np.array([0, 255, 0]),
    "red": np.array([255, 0, 0]),
    "blue": np.array([0, 0, 255]),
}

def chroma_key(input_path, output_path, key_color="green", tolerance_ratio=1.3, min_brightness=80):
    if key_color not in COLORS:
        raise ValueError(f"Unknown color '{key_color}'. Use: green, red, blue")

    target = COLORS[key_color]
    img = Image.open(input_path).convert("RGB")
    pixels = np.array(img).astype(np.float32)
    h, w = pixels.shape[:2]
    r, g, b = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]

    if key_color == "green":
        mask = (g > r * tolerance_ratio) & (g > b * tolerance_ratio) & (g > min_brightness)
    elif key_color == "red":
        mask = (r > g * tolerance_ratio) & (r > b * tolerance_ratio) & (r > min_brightness)
    elif key_color == "blue":
        mask = (b > r * tolerance_ratio) & (b > g * tolerance_ratio) & (b > min_brightness)

    alpha = np.where(mask, 0, 255).astype(np.uint8)
    fg = ~mask

    # Despill: clamp dominant channel for foreground pixels
    if key_color == "green":
        pixels[:, :, 1] = np.where(fg, np.minimum(g, (r + b) / 2.0), g)
    elif key_color == "red":
        pixels[:, :, 0] = np.where(fg, np.minimum(r, (g + b) / 2.0), r)
    elif key_color == "blue":
        pixels[:, :, 2] = np.where(fg, np.minimum(b, (r + g) / 2.0), b)

    pixels = np.clip(pixels, 0, 255).astype(np.uint8)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = pixels
    rgba[:, :, 3] = alpha

    Image.fromarray(rgba, "RGBA").save(output_path)
    bg_pct = 100 * np.sum(mask) / (h * w)
    print(f"Chroma-key ({key_color}): {bg_pct:.0f}% keyed, saved to {output_path}", flush=True)
    return bg_pct


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python chroma_key.py <input> <output> [green|red|blue]")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2]
    color = sys.argv[3] if len(sys.argv) > 3 else "green"
    chroma_key(inp, out, color)
