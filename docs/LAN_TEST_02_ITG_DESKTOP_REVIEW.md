# 🔴 Desktop AI Review — LAN Test #02 ITG 2-Machine Plan

**Date:** May 25, 2026 | **Reviewer:** Desktop AI | **Verdict:** 🛑 **BLOCKED — 5 critical blockers, cannot execute as written**

---

## 🔴 CRITICAL BLOCKERS (Test cannot proceed)

### 1. `itg_splitter.py` hardcodes `127.0.0.1` — Desktop can NEVER reach Laptop ComfyUI

**File:** `src/itg_splitter.py:20-22`

```python
def _comfy_url(port=None):
    p = port or COMFYUI_PORT
    return f"http://127.0.0.1:{p}"
```

`split_image_into_n_layers` accepts `comfyui_port` but the HOST is hardcoded to `127.0.0.1`. The Desktop Worker cannot use `http://10.0.0.5:8188` — it will always try localhost, where Desktop has no ComfyUI instance.

**Fix:** Add a `comfyui_host` parameter to `split_image_into_n_layers` and `_comfy_url`.

---

### 2. GUI ITG buttons are ALL stubs — Nir's clicks do nothing

**File:** `src/gui.py`

| GUI Widget | Method | Line | What Happens |
|---|---|---|---|
| Boss `split_and_process` | `BossWidget_ITG.split_and_process()` | 1445 | Prints "run via terminal with src/itg_node.py for now" (ERROR) |
| Boss `arrange_zorder` | `BossWidget_ITG.arrange_zorder()` | 1449 | Prints "run via terminal with src/itg_node.py for now" (ERROR) |
| Worker `split_task` | `WorkerWidget_ITG.split_task()` | 1564 | Prints "ITG split -- use src/itg_node.py terminal interface" |
| Worker `upload_results` | `WorkerWidget_ITG.upload_results()` | 1568 | Prints "Upload -- use src/itg_node.py terminal interface" |

The test plan has Nir clicking these buttons in 7 steps expecting real work to happen. **Nothing happens.**

---

### 3. "Auto-Pilot" and "Auto-Process" checkboxes DO NOT EXIST in ITG GUI

Test plan Step 1 says: `✅ Check: "Auto-Pilot"`  
Test plan Step 2 says: `✅ Check: "Auto-Process"`  

Neither checkbox exists in `BossWidget_ITG` or `WorkerWidget_ITG`. These exist in the TTG GUI widgets but were never added to the ITG ones.

---

### 4. Question submission creates NO root tasks — pipeline has no entry point

**Flow:**
1. Client uploads image → `upload_itg_question()` (app.py:118) creates a `Question` row
2. **No `Task` rows are created.** The Question sits in `pending` state with zero tasks.
3. Boss polls `/api/tasks?status=pending&type=ITG` → returns empty `[]`
4. Boss sees nothing. Can't split. Can't create children.

In TTG, the Boss clicks "Split" which calls `/api/question/<id>/split` → creates 6 tasks. For ITG, there is **no equivalent mechanism** to create the root task (depth=0, parent_task_id=None).

**Fix needed:** Either `upload_itg_question` must auto-create a root task, OR the Boss must have a "Create Root Task" button that creates one from the selected question.

---

### 5. Boss can't mark its own task complete — `/api/task/<id>/result` requires image files

**File:** `src/itg_node.py:194-198`

```python
# Boss marks task complete after creating children
self._api("POST", f"/api/task/{task['id']}/result",
          data={"split_result_1": ..., "split_result_2": ...})
```

**File:** `src/app.py:390-402`

```python
def submit_result(task_id):
    images = request.files.getlist("images")
    if not images:
        return jsonify({"error": "at least one image file is required"}), 400
```

Boss ITG sends form data (split_result_1/2) — NO image files. The endpoint rejects it with HTTP 400. Boss task stays in CLAIMED state forever.

---

## 🟡 HIGH ISSUES (Will break test flow)

### 6. `_auto_complete_question` checks depth=0 only — ITG completes prematurely

**File:** `src/app.py:436-444`

```python
direct_children = Task.query.filter_by(question_id=question.id, depth=0).all()
if direct_children and all(t.status == TaskStatus.COMPLETED for t in direct_children):
    question.status = QuestionStatus.COMPLETED
```

ITG leaf results are at **depth=max_depth (2)**, not depth 0. The root task (depth 0) completes as soon as it creates children. This means the Question would be marked COMPLETED **before the leaf workers finish**. The download ZIP would show 0 layers.

---

### 7. Download ZIP queries wrong task structure for ITG

**File:** `src/app.py:615`

```python
tasks = Task.query.filter_by(question_id=question_id, depth=0).order_by(Task.layer_number).all()
```

ITG final layers are NOT at depth=0 and do NOT have `layer_number` set. The download would return an empty or wrong ZIP.

---

### 8. Boss `load_children` queries `parent_task_id=0` — misses ITG task tree

**File:** `src/gui.py:1430`

```python
r = requests.get(f"{self.get_server()}/api/tasks?parent_task_id=0&type=ITG", timeout=10)
```

Root ITG tasks likely have `parent_task_id=None` (not 0). And child tasks have non-zero parent IDs. Either way, this query returns nothing for the ITG tree structure.

---

## 🔵 MINOR ISSUES

### 9. Dual-garbage path leaves parent in CLAIMED state forever

`itg_node.py:118-140` — When both layers are garbage, a fallback child is created but the parent task is never marked complete/failed. It stays CLAIMED and pollutes task queries.

### 10. `submit_result` has competing file checks

`app.py:398-399` — Checks both `request.files.getlist("images")` and `request.files["image"]`. If a Worker sends files under a different key, it breaks.

### 11. Ollama hardcoded to `localhost:11434`

`itg_judge.py:9` — `OLLAMA_URL = "http://localhost:11434/api/chat"`. Desktop Worker needs to use Laptop's Ollama OR its own. Either way, this isn't configurable.

---

## 📊 SUMMARY — What Would It Take to Fix?

| Issue | Fix Complexity | Required for Test? |
|---|---|---|
| #1 Hardcoded 127.0.0.1 | Small (add host param) | YES |
| #2 GUI stubs | Large (wire itg_node.py into Qt) | YES if GUI test |
| #3 Missing checkboxes | Small (add QCheckBox) | YES |
| #4 No root task creation | Medium (auto-create on upload) | YES |
| #5 Result endpoint rejects Boss | Small (allow form-only submit) | YES |
| #6 Premature completion | Small (check all depths) | YES |
| #7 Bad ZIP query | Small (query all tasks) | YES |
| #8 load_children wrong query | Small (use question tree API) | YES |

---

## 💡 RECOMMENDATION

**Option A — Quick CLI Test (bypass GUI):**
- Fix #1 (ComfyUI host), #4 (root task creation), #5 (result endpoint), #6 (auto-complete), #7 (ZIP download)
- Run everything via `itg_node.py` terminal commands on both machines
- ~1 hour of fixes, 15 min test

**Option B — Full GUI Test (as planned):**
- Fix ALL 8 issues above + wire itg_node.py logic into Qt buttons + add auto-pilot/auto-process
- ~4-6 hours of work

**Desktop is ready to implement either option — your call, Laptop.** 🫡
