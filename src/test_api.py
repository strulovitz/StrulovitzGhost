import requests
import time
import os
import sys

BASE = "http://localhost:5000"
PASS = 0
FAIL = 0


def check(step, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {step} {detail}")
    else:
        FAIL += 1
        print(f"  ❌ {step} {detail}")


print("1. Submit a question...")
r = requests.post(
    f"{BASE}/api/question",
    json={
        "description": "The group camps in a moonlit forest clearing. Stars fill the sky above mountains. Ancient oaks surround them. Tiefling fighter sharpens her sword. Dragonborn wizard studies spells. Dwarf cleric and Halfling thief argue over a campfire. Elf paladin and Human druid gossip on a log.",
        "style": "Ghibli animation",
    },
    timeout=10,
)
check("POST /api/question", r.status_code == 201, f"id={r.json()['id']}, style={r.json().get('style')}")
qid = r.json()["id"]

print("\n2. Get the question...")
r = requests.get(f"{BASE}/api/question/{qid}", timeout=10)
check("GET /api/question/{id}", r.status_code == 200, f"status={r.json()['status']}")

print("\n3. Boss creates tasks manually (no LLM)...")
r = requests.post(
    f"{BASE}/api/task",
    json={
        "question_id": qid,
        "tasks": [
            {"layer_number": 6, "prompt": "Ghibli animation style: night sky with stars and full moon, snow-capped mountains on horizon. Transparent background."},
            {"layer_number": 5, "prompt": "Ghibli animation style: magical ancient oak forest, glowing motes, tree line around clearing. Transparent background."},
            {"layer_number": 4, "prompt": "Ghibli animation style: Tiefling fighter girl sharpening sword on rock, Dragonborn wizard guy reading spellbook on rock, medium flower patches. Transparent background."},
            {"layer_number": 3, "prompt": "Ghibli animation style: Dwarf cleric guy and Halfling thief guy arguing over campfire with roasting wild pig, closer flowers. Transparent background."},
            {"layer_number": 2, "prompt": "Ghibli animation style: Elf paladin girl and Human druid girl sitting on fallen log, backs to viewer, gossiping, backpacks. Transparent background."},
            {"layer_number": 1, "prompt": "Ghibli animation style: very close tree branches framing scene from edges, owl on branch, rabbit on root looking at camp. Transparent background."},
        ],
    },
    timeout=10,
)
check("POST /api/task", r.status_code == 201, f"tasks={len(r.json().get('tasks', []))}")
tasks = r.json().get("tasks", [])

print("\n4. Worker polls for pending tasks...")
r = requests.get(f"{BASE}/api/tasks?status=pending", timeout=10)
check("GET /api/tasks?status=pending", r.status_code == 200, f"found={len(r.json())}")

print("\n5. Worker claims and uploads each task...")
for t in tasks:
    tid = t["id"]
    layer = t["layer_number"]

    r = requests.post(
        f"{BASE}/api/task/{tid}/claim",
        json={"worker_id": f"worker-{layer}"},
        timeout=10,
    )
    check(f"  Claim Layer {layer}", r.status_code == 200, f"task={tid}")

    png_path = os.path.join(os.path.dirname(__file__), "output", f"placeholder_layer{layer}.png")
    if os.path.exists(png_path):
        with open(png_path, "rb") as f:
            r = requests.post(
                f"{BASE}/api/task/{tid}/result",
                files={"image": f},
                timeout=10,
            )
        check(f"  Upload Layer {layer}", r.status_code == 200, f"filename={r.json().get('result_filename')}")
    else:
        check(f"  Upload Layer {layer}", False, "PNG not found")

print("\n6. Verify question completed...")
r = requests.get(f"{BASE}/api/question/{qid}", timeout=10)
check("Question completed?", r.json()["status"] == "completed" and r.json()["completed_at"] is not None)

print(f"\n{'='*40}")
print(f"Results: {PASS} passed, {FAIL} failed")
print(f"{'='*40}")

sys.exit(0 if FAIL == 0 else 1)
