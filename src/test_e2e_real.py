import sys, os, requests, time
sys.path.insert(0, os.path.dirname(__file__))

BASE = "http://localhost:5000"

SCENE = """The group makes camp in a moonlit forest clearing. Stars and moon fill the night sky above snow-capped mountains. Ancient magical oak trees surround the clearing. The Tiefling fighter girl sharpens her sword on a rock. The Dragonborn wizard guy reads his spellbook nearby."""

print("=" * 50)
print("  STRULOVITZ GHOST - REAL AI E2E TEST")
print("=" * 50)

print("\n1. Submit question...")
r = requests.post(f"{BASE}/api/question", json={"description": SCENE, "style": "Ghibli animation"}, timeout=10)
assert r.status_code == 201, f"Submit failed: {r.text}"
qid = r.json()["id"]
print(f"   Question #{qid} submitted ✅")

print("\n2. Boss creates 6 tasks...")
tasks_data = [
    {"layer_number": 6, "prompt": "Ghibli animation: night sky with bright full moon, scattered stars, subtle clouds, snow-capped mountain peaks on horizon. Everything else transparent."},
    {"layer_number": 5, "prompt": "Ghibli animation: ancient magical oak trees surrounding a clearing, thick trunks, sprawling branches, glowing motes. Dark forest shadows. Everything else transparent."},
    {"layer_number": 4, "prompt": "Ghibli animation: Tiefling fighter girl with horns and tail sitting on a rounded rock, sharpening sword with whetstone, focused expression. Dragonborn wizard guy with dragon scales sitting on rock nearby, reading spellbook. Medium flower patches. Everything else transparent."},
    {"layer_number": 3, "prompt": "Ghibli animation: Dwarf cleric in armor with holy symbol standing, gesturing. Halfling thief opposite him, defensive but mischievous. Small campfire between them with roasting wild pig. Closer flowers. Everything else transparent."},
    {"layer_number": 2, "prompt": "Ghibli animation: Elf paladin girl and Human druid girl sitting on fallen tree log, backs to viewer, gossiping and laughing. Backpacks and blankets neatly on log. Everything else transparent."},
    {"layer_number": 1, "prompt": "Ghibli animation: very close tree branch tips from edges framing scene. Owl sitting on branch watching. Curious rabbit on thick tree root at ground, back to viewer. Everything else transparent."},
]
r = requests.post(f"{BASE}/api/task", json={"question_id": qid, "tasks": tasks_data}, timeout=10)
assert r.status_code == 201
print(f"   6 tasks created ✅")

print("\n3. Generate Layer 4 with REAL Qwen AI (other 5 with placeholders)...")
from generator import generate_diffusers
from PIL import Image

output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)

tasks = r.json()["tasks"]

for t in tasks:
    tid = t["id"]
    layer = t["layer_number"]
    prompt = t["prompt"]

    r2 = requests.post(f"{BASE}/api/task/{tid}/claim", json={"worker_id": f"worker-{layer}"}, timeout=10)
    assert r2.status_code == 200, f"Claim failed for layer {layer}"

    if layer == 4:
        print(f"   🔥 Generating Layer {layer} with REAL Qwen AI (4-bit, ~3 min)...")
        png_path = os.path.join(output_dir, f"e2e_real_layer{layer}.png")
        result = generate_diffusers(prompt, png_path, width=512, height=384, num_steps=12)
        assert result, f"Generation failed for layer {layer}"
        print(f"   Layer {layer} generated ✅")
    else:
        png_path = os.path.join(output_dir, f"placeholder_layer{layer}.png")
        print(f"   Layer {layer}: using placeholder")

    with open(png_path, "rb") as f:
        r3 = requests.post(f"{BASE}/api/task/{tid}/result", files={"image": f}, timeout=10)
    assert r3.status_code == 200, f"Upload failed for layer {layer}: {r3.text}"
    print(f"   Layer {layer} uploaded ✅")

print("\n4. Verify question completed...")
r = requests.get(f"{BASE}/api/question/{qid}", timeout=10)
q = r.json()
assert q["status"] == "completed", f"Status: {q['status']}"
assert q["completed_at"] is not None
print(f"   Question #{qid} COMPLETED ✅")

print(f"\n{'=' * 50}")
print("  ALL TESTS PASSED! 🎉👻✨")
print(f"{'=' * 50}")
