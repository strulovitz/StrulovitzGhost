import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

log_path = os.path.join(os.path.dirname(__file__), "output", "test_log.txt")

def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    print(msg, flush=True)

log("=" * 40)
log("TEST: Real D&D Layer 4 with distance hints")
log("=" * 40)

from PIL import Image
from generator import generate_diffusers

CANVAS_W = 512
CANVAS_H = 384

PROMPT = (
    "Ghibli animation style. "
    "The background is soft green grass with scattered flower patches, "
    "drawn as if viewed from 20 meters away — the grass appears as a smooth texture, "
    "flowers are tiny dots, filling the lower two-thirds of the frame. "
    "On this grass, sitting on a small rounded rock: a Tiefling fighter girl with horns and tail, "
    "sharpening her sword with a whetstone. "
    "On another rock nearby: a Dragonborn wizard guy with dragon scales, reading a spellbook. "
    "Both characters are small figures in the center of the scene. "
    "Green screen background behind everything. Clean edges. Isolated subjects."
)

temp = os.path.join(os.path.dirname(__file__), "output", "_temp_layer4.png")
final = os.path.join(os.path.dirname(__file__), "output", "layer4_real_70pct.png")

log("Step 1: Generating with Qwen AI...")
log(f"Prompt: {PROMPT[:100]}...")

try:
    result = generate_diffusers(
        PROMPT, temp,
        width=512, height=384,
        num_steps=15,
        remove_bg=True,
    )
    if not result:
        log("FAILED: generate_diffusers returned None")
        sys.exit(1)
    log(f"Generated: {temp}")
except Exception as e:
    log(f"ERROR: {e}")
    import traceback
    log(traceback.format_exc())
    sys.exit(1)

log("Step 2: Scale to 70% and center...")
try:
    obj = Image.open(temp).convert("RGBA")
    new_w = int(obj.width * 70 / 100)
    new_h = int(obj.height * 70 / 100)
    obj = obj.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    x = (CANVAS_W - new_w) // 2
    y = (CANVAS_H - new_h) // 2
    canvas.paste(obj, (x, y), obj)
    canvas.save(final)
    log(f"Saved: {final}")
except Exception as e:
    log(f"Scale error: {e}")

log("DONE!")
