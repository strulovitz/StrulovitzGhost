import sys
from PIL import Image
import numpy as np

INPUT = "output/layer1_green.png"
OUTPUT = "output/layer1.png"

print(f"Loading {INPUT}...", flush=True)
img = Image.open(INPUT).convert("RGB")
pixels = np.array(img).astype(np.float32)
h, w, _ = pixels.shape
print(f"Image: {w}x{h}", flush=True)
total = h * w

r, g, b = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]

# Green screen detection: green channel dominates AND is bright enough
# A pixel is "green screen" if: g > r * 1.3 AND g > b * 1.3 AND g > 80
green_dominates = (g > r * 1.3) & (g > b * 1.3)
green_bright = g > 80
green_mask = green_dominates & green_bright

bg_count = np.sum(green_mask)
fg_count = total - bg_count
print(f"Green screen: {bg_count} pixels ({100*bg_count/total:.0f}%)", flush=True)
print(f"Foreground:  {fg_count} pixels ({100*fg_count/total:.0f}%)", flush=True)

alpha = np.where(green_mask, 0, 255).astype(np.uint8)

# Despill: clamp green to average of r+b for KEPT pixels only
foreground = ~green_mask
g_despilled = np.where(foreground, np.minimum(g, (r + b) / 2.0), g)
pixels[:, :, 1] = g_despilled

pixels = np.clip(pixels, 0, 255).astype(np.uint8)

# RGBA output
rgba = np.zeros((h, w, 4), dtype=np.uint8)
rgba[:, :, :3] = pixels
rgba[:, :, 3] = alpha

result = Image.fromarray(rgba, "RGBA")
result.save(OUTPUT)
print(f"Saved: {OUTPUT}", flush=True)
