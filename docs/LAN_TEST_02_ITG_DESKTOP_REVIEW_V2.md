# 🔴 Desktop AI Review v2 — LAN Test #02 ITG (CORRECTED)

**Date:** May 25, 2026 | **Reviewer:** Desktop AI | **Verdict:** 🟡 6 real bugs, 1 critical

> ⚠️ v1 review (since deleted) falsely reported Issues #2 and #3 based on stale local files.
> The GUI IS fully wired with Auto-Pilot, Auto-Process, ITGSplitThread. Confirmed on current master.

---

## 🔴 CRITICAL (Test blocked)

### 1. `itg_splitter.py:20-22` — Hardcoded `127.0.0.1` host

```python
def _comfy_url(port=None):
    p = port or COMFYUI_PORT
    return f"http://127.0.0.1:{p}"
```

**Why it blocks:** The GUI `ITGSplitThread.run()` (gui.py:1841-1843) extracts only the **port** from the ComfyUI URL and passes it to `split_image_into_n_layers(comfyui_port=port)`. The host (`10.0.0.5`) is **discarded**. Desktop Worker will always try `http://127.0.0.1:8188` — localhost, where Desktop has no ComfyUI.

**Fix:** Add a `comfyui_host` parameter to `_comfy_url` and `split_image_into_n_layers`, or pass the full URL through the function chain.

**Files:**
- `src/itg_splitter.py` lines 20, 25, 35, 43, 49, 74
- `src/gui.py` lines 1840-1844 (only port extracted)

---

## 🟡 HIGH (Will break parts of the test)

### 2. `submit_result` require images → non-leaf tasks can't complete (app.py:397-402)

```python
images = request.files.getlist("images")
if not images:
    images = [request.files["image"]] if "image" in request.files else []
if not images:
    return jsonify({"error": "at least one image file is required"}), 400
```

Non-leaf tasks (depth < max_depth) call `submit_result` with `data=split_data` only — no image files:
- Boss: `gui.py:1649` — `data=split_data`
- Worker: `gui.py:2169` — `data=split_data`

**Result:** HTTP 400 error. Tasks stay `CLAIMED` forever.

**Impact:** `_auto_complete_question` depends on depth=0 tasks being COMPLETED (see Bug #3). Tasks accumulate in CLAIMED state. Mitigated by the Boss manually completing the question via `/api/question/<id>/complete`.

**Fix:** Allow `submit_result` to accept form-only requests for non-leaf tasks, OR split the form-data save into its own endpoint.

---

### 3. `_auto_complete_question` only checks depth=0 (app.py:439)

```python
direct_children = Task.query.filter_by(question_id=question.id, depth=0).all()
if direct_children and all(t.status == TaskStatus.COMPLETED for t in direct_children):
    question.status = QuestionStatus.COMPLETED
```

ITG leaf results are at **depth=max_depth (2)**. Auto-complete never considers them. Combined with Bug #2 (depth=0 tasks never COMPLETED), auto-complete effectively never fires for ITG.

**Impact:** Question never auto-completes. The Boss manually completes via `/api/question/<id>/complete` in `arrange_zorder` → test works, but auto-completion is dead code for ITG.

**Fix:** Change to check ALL tasks for the question (any depth), or at least check that all non-failed leaf nodes are COMPLETED.

---

### 4. Download ZIP queries wrong task structure for ITG (app.py:615)

```python
tasks = Task.query.filter_by(question_id=question_id, depth=0).order_by(Task.layer_number).all()
```

Three problems:
1. ITG final layers are at **depth=2**, not depth=0
2. ITG tasks have no `layer_number` set
3. Even if tasks were found, `result_filename` is likely empty (Bug #2 prevents completion)

The actual final 6 layers are uploaded by Boss via `/api/question/<id>/complete` to `ITG_FINAL` directory, but the ZIP endpoint reads from task `result_filename` columns.

**Impact:** Step 7 "Download Layers (ZIP)" returns empty ZIP or wrong files. Test will show 0 layers in the downloaded ZIP.

**Fix:** Either change the ZIP query to search ITG_FINAL directory for question files, OR add a `/question/<id>/layers/download` that reads from the final directory.

---

## 🔵 MEDIUM

### 5. `BossWidget_ITG.load_children` queries `parent_task_id=0` (gui.py:1485)

```python
r = requests.get(f"{self.get_server()}/api/tasks?parent_task_id=0&type=ITG", timeout=10)
```

Root ITG tasks have `parent_task_id=None` (not 0). Child tasks have non-zero parent IDs. This query returns nothing.

**Impact:** Manual "Children" list in Boss GUI shows empty. Auto-pilot `arrange_zorder` uses the correct `/api/question/<id>/tree` endpoint (gui.py:1688) → works fine. Only affects manual mode.

**Fix:** Change to query by `question_id` instead of `parent_task_id=0`, or use the tree endpoint.

---

## 🔵 LOW

### 6. `submit_result` form data handler is dead code (app.py:421-427)

```python
if data := request.form:
    if data.get("split_result_1"):
        task.split_result_1 = data["split_result_1"]
    ...
```

This code is **never reached**:
- For leaf tasks: `split_data` is sent in a separate POST that arrives AFTER the task is already COMPLETED → hits 409 at line 394
- For non-leaf tasks: `split_data` is sent in the sole POST, but it fails at line 401-402 ("no image files") before reaching line 421

**Impact:** `split_result_1` and `split_result_2` fields are never populated. Not blocking — they're just metadata.

**Fix:** Move form handling above the file check, or handle non-leaf task completion separately.

---

## ✅ WHAT WORKS (confirmed correct)

| Component | Status | Notes |
|---|---|---|
| Client uploads image → Question created | ✅ | `/api/question/upload` works |
| Boss Auto-Pilot checkbox + state machine | ✅ | gui.py:1376, 1437-1507 |
| Boss creates root task via `/api/tasks/batch` | ✅ | gui.py:1546-1558 |
| ITGSplitThread (split+judge+upload) | ✅ | gui.py:1791-1912 |
| Worker Auto-Process checkbox | ✅ | gui.py:1971, auto-splits on claim |
| Polling (Boss timer 3s, Worker timer 5s, Client timer 5s) | ✅ | |
| Children created via `/api/tasks/batch` | ✅ | Boss + Worker both create children |
| Z-order → reduce to 6 → upload via `/api/question/<id>/complete` | ✅ | gui.py:1671-1765 |
| Leaf task final result upload (files) | ✅ | gui.py:2133-2142 |
| Ollama vision judging (local) | ✅ | Requires qwen3-vl:4b on each machine |
| Question tree endpoint (`/api/question/<id>/tree`) | ✅ | Used by Boss Z-order |

---

## 📊 FIX PRIORITY

| # | Bug | Fix Size | Blocker? |
|---|---|---|---|
| 1 | Hardcoded 127.0.0.1 | Small (add host param) | **YES** — Desktop can't split |
| 4 | ZIP download wrong query | Small (fix directory scan) | **YES** — Step 7 fails |
| 2 | Non-leaf result endpoint 400 | Small (allow form-only) | Sort of — CLAIMED state mess |
| 3 | Auto-complete depth=0 only | Small (check all depths) | No — Boss manually completes |
| 5 | load_children query wrong | Small (use question_id) | No — auto-pilot bypasses |

**Estimated fix time:** ~1-2 hours for all 5 bugs.

---

## 💡 RECOMMENDATION

Fix bugs #1 and #4 minimally, run the test. #2, #3, #5 are non-blocking for a first test run. Desktop is ready to implement fixes — your call, Laptop. 🫡
