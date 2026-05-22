"""Quick smoke test for Phase 1 DB + API changes."""
import sys, os, json, io
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import Question, Task, JobType, QuestionStatus, TaskStatus
from PIL import Image

with app.app_context():
    db.drop_all()
    db.create_all()

client = app.test_client()

# Test 1: Create TTG question
resp = client.post("/api/question", json={
    "type": "TTG",
    "description": "A moonlit forest clearing",
    "style": "Ghibli animation",
    "global_negative_prompt": "watermark, signature",
    "max_depth": 1,
})
assert resp.status_code == 201, f"TTG create failed: {resp.data}"
qid = resp.json["id"]
assert resp.json["type"] == "TTG"
print(f"[PASS] 1: TTG question created (id={qid})")

# Test 2: List questions with type filter
resp = client.get("/api/questions?type=TTG")
assert resp.status_code == 200
assert len(resp.json) == 1
print("[PASS] 2: Filter questions by type")

# Test 3: Create tasks batch (ITG style)
resp = client.post("/api/tasks/batch", json={
    "tasks": [
        {"question_id": qid, "type": "ITG", "depth": 1, "max_depth": 2,
         "prompt": "Decompose sky", "input_image": "task_1_01.png"}
    ]
})
assert resp.status_code == 201
assert len(resp.json) == 1
task_id = resp.json[0]["id"]
print(f"[PASS] 3: Batch task created (task_id={task_id})")

# Test 4: Get task children (empty)
resp = client.get(f"/api/task/{task_id}/children")
assert resp.status_code == 200
assert resp.json == []
print("[PASS] 4: Children endpoint works")

# Test 5: Claim task
resp = client.post(f"/api/task/{task_id}/claim", json={"worker_id": "test_worker"})
assert resp.status_code == 200
assert resp.json["status"] == "claimed"
assert resp.json["worker_id"] == "test_worker"
print("[PASS] 5: Task claimed")

# Test 6: Set Z-order
resp = client.put(f"/api/task/{task_id}/zorder", json={
    "layers": ["task_1_01_02.png", "task_1_01_01.png"]
})
assert resp.status_code == 200
print("[PASS] 6: Z-order set")

# Test 7: Submit result (single image)
img = Image.new("RGBA", (64, 64), (0, 255, 0, 128))
buf = io.BytesIO()
img.save(buf, "PNG")
buf.seek(0)
resp = client.post(f"/api/task/{task_id}/result",
    data={"image": (buf, "result.png")},
    content_type="multipart/form-data")
assert resp.status_code == 200
assert resp.json["status"] == "completed"
print("[PASS] 7: Result submitted, task completed")

# Test 8: Task tree
resp = client.get(f"/api/question/{qid}/tree")
assert resp.status_code == 200
assert "tree" in resp.json
print("[PASS] 8: Tree endpoint works")

# Test 9: Stats
resp = client.get(f"/api/question/{qid}/stats")
assert resp.status_code == 200
assert resp.json["completed"] >= 1
print("[PASS] 9: Stats endpoint works")

# Test 10: Health
resp = client.get("/api/health")
assert resp.status_code == 200
assert "disk_free_gb" in resp.json
print(f"[PASS] 10: Health ({resp.json['disk_free_gb']} GB free)")

# Test 11: File upload
img2 = Image.new("RGBA", (64, 64), (0, 255, 0, 128))
buf2 = io.BytesIO()
img2.save(buf2, "PNG")
buf2.seek(0)
resp = client.post("/api/files/upload",
    data={"file": (buf2, "test.png"), "task_id": "99"},
    content_type="multipart/form-data")
assert resp.status_code == 200
fname = resp.json["filename"]
print(f"[PASS] 11: File uploaded ({fname})")

# Test 12: File download
resp = client.get(f"/api/files/{fname}")
assert resp.status_code == 200
print("[PASS] 12: File downloaded")

# Test 13: Cleanup
resp = client.delete(f"/api/question/{qid}/cleanup")
assert resp.status_code == 200
print("[PASS] 13: Cleanup OK")

# Test 14: Cannot reset completed task
resp = client.post(f"/api/task/{task_id}/reset")
assert resp.status_code == 409
print("[PASS] 14: Cannot reset completed task")

# Test 15: Retry limit — claim then reset 3 times
resp2 = client.post("/api/tasks/batch", json={
    "tasks": [{"question_id": qid, "type": "ITG", "depth": 2, "prompt": "test retry"}]
})
tid2 = resp2.json[0]["id"]
client.post(f"/api/task/{tid2}/claim", json={"worker_id": "test"})
for i in range(4):
    r = client.post(f"/api/task/{tid2}/reset")
    if r.json.get("status") == "failed":
        break
resp = client.get(f"/api/task/{tid2}")
data = resp.json
assert data is not None and (data.get("status") == "failed" or data.get("retry_count", 0) >= 3)
print(f"[PASS] 15: Retry limit works (retry_count={data.get('retry_count')})")

# Test 16: ITG upload question
img_buf = io.BytesIO()
Image.new("RGBA", (128, 128), (255, 0, 0, 255)).save(img_buf, "PNG")
img_buf.seek(0)
resp = client.post("/api/question/upload",
    data={"file": (img_buf, "painting.png"), "max_depth": "2", "description": "Test painting"},
    content_type="multipart/form-data")
assert resp.status_code == 201
assert resp.json["type"] == "ITG"
print(f"[PASS] 16: ITG question uploaded (id={resp.json['id']})")

# Test 17: List ITG tasks
resp = client.get("/api/tasks?type=ITG")
assert resp.status_code == 200
print(f"[PASS] 17: ITG tasks list ({len(resp.json)} pending)")

print("\n*** ALL 17 TESTS PASSED! Phase 1 DB + API is solid. ***")
