# 🔧 ITG GUI Wiring Plan

**Status:** DRAFT — pending Desktop AI review via seance

---

## ⛔⛔⛔ NOT BUILDING YET — READ THIS FIRST ⛔⛔⛔

**These features are intentionally SKIPPED in this build. They are tracked in MEMORY.md and will be built later. DO NOT expect them to work when testing:**

| # | Skipped Feature | Why | Impact |
|---|----------------|-----|--------|
| 1 | **Mid-level Boss Z-ordering** | `itg_node.py` doesn't do it either — creates children, marks self done, never waits for children. Complex to implement. | Only Top Boss (depth 0) does Z-ordering. Works fine for depth ≤ 2. |
| 2 | **Multi-level recursive splitting (depth > 2)** | Each depth level doubles the tasks. Depth 2 already creates up to 7 nodes. Beyond that is exponential. | Test will use max_depth=2 only. |
| 3 | **Mid-level node waiting for children completion** | Nodes don't poll for children status. They fire-and-forget. | Only Top Boss collects final results. |
| 4 | **Per-level Z-order upload** (`PUT /api/task/{id}/zorder`) | The Z-order endpoint exists in app.py but is never called by any code. | Top Boss does one final Z-ordering from all leaf results. |
| 5 | **ComfyUI intermediate progress bar** | ComfyUI API only reports "done" or "error" — no intermediate progress. | GUI shows "Splitting... (X seconds elapsed)" with a pulsing bar, not a real percentage. |
| 6 | **Multiple ComfyUI instances / GPU pool** | Only one ComfyUI per machine. Splits are serialized. | If two tasks need splitting on same machine, second one waits. GUI shows "ComfyUI busy." |
| 7 | **ITG scene_viewer.py integration** | Existing scene_viewer only handles TTG layers. | ITG layers viewable as regular PNGs but no special viewer. |
| 8 | **Client auto-polling for completion** | Client tab currently has no poll timer. | Client must manually click "Refresh." Timer can be added after. |
| 9 | **Boss "Arrange Z-Order" button** | Currently always disabled. | Will be wired to call `determine_z_order()` but only after children complete. |
| 10 | **Error recovery for failed branches** | If a sub-branch fails (dual-garbage ×3), it gets marked "failed" and is skipped. No automatic rebalancing. | Fewer than 6 layers possible. Empty transparent layers fill the gap. |

**⚠️ IF YOU'RE TESTING AND SOMETHING FROM THIS LIST DOESN'T WORK — IT'S NOT A BUG. IT'S NOT BUILT YET. CHECK THIS LIST FIRST.**

---

## 🎯 Goal

Wire up the ITG Boss and Worker GUI tabs so Lan Test #02 can run as a GUI clicking experience (like Lan Test #01 for TTG).

**Current state:** Client tab works ✅. Boss and Worker tabs have UI elements but core methods are stubs printing "use terminal instead."

---

## 🧱 Architecture: What ITG Actually Does

ITG uses a **pool model** (not flat like TTG):

1. Client uploads image → server creates pending Question
2. **Boss (depth 0):** Claims question, creates root task, splits image 1→2, judges quality, creates 2 child tasks at depth 1
3. **Workers (depth 1+):** Claim pending tasks, split 1→2, judge, upload
4. **Bottom workers (depth ≥ max_depth):** Upload final result PNGs
5. **Top Boss:** When all children complete, combine to exactly 6 layers, upload to `/api/question/{id}/complete`
6. Client downloads 6 layer ZIP

Each node needs: ComfyUI (for splitting) + Ollama qwen3-vl (for quality judging).

---

## 📦 What to Build (3 Phases)

### PHASE 1: ITG Worker GUI 🔧 (biggest priority)

The Worker tab needs to go from stub → fully functional.

**New class: `ITGSplitThread(QThread)`**
```python
signals:
    progress_signal(str)              # "Downloading input...", "Splitting (20s elapsed)...", "Judging layer 1..."
    layer_preview_signal(str, bool)   # path, is_good
    finished_signal(list, list)       # good_paths, judgments
    error_signal(str)
```

**What `run()` does:**
1. Download input image from server
2. Call `split_image_into_n_layers()` (blocks 25s-10min via ComfyUI)
3. Call `judge_layer_quality()` for each of 2 layers
4. Emit previews for each layer
5. Return good_layer_paths + judgments

**New UI elements to add:**
- Image preview QLabel (shows downloaded input, then split results)
- QProgressBar (for split duration feedback)
- "Auto-Claim" checkbox (automatically claims when polling finds a task)

**Rewire existing:**
- `split_task()` → creates `ITGSplitThread`, connects signals, starts
- `upload_results()` → POSTs good layers to `/api/files/upload`, then POSTs final result to `/api/task/{id}/result`
- On split error → `POST /api/task/{id}/reset`, re-poll

---

### PHASE 2: ITG Boss GUI 👑 

The Boss needs to create root tasks and split the original image.

**New method: `_boss_poll()` (auto-pilot timer)**

Mirrors TTG Boss pattern:
1. Polls `GET /api/questions?type=ITG&status=pending` every 3s
2. When question found: creates root task via `POST /api/tasks/batch` with `{depth: 0, max_depth: N, input_image: original_filename, prompt: ""}`
3. Claims root task: `POST /api/task/{id}/claim`
4. Spawns `ITGSplitThread` (same thread class as Worker)
5. On finish: if depth < max_depth → create children via `POST /api/tasks/batch`
6. If depth ≥ max_depth (shouldn't happen for Boss) → upload final result

**New UI elements:**
- "Auto-Pilot" checkbox (mirrors TTG Boss)
- Split result previews (2 QLabels showing layer A and layer B)

**Rewire existing:**
- `split_and_process()` → calls real split flow (not stub message)
- `arrange_zorder()` → calls `determine_z_order()` then `PUT /api/task/{id}/zorder`

---

### PHASE 3: Final Combine + Client Download 🎁

**Top Boss combining:**
After all depth 0 children complete:
1. Download all child result files
2. Call `reduce_to_6_layers(z_ordered_paths, output_dir)` → exactly 6 PNGs
3. Upload via `POST /api/question/{id}/complete` (multipart: 6 images)

**Client auto-poll:**
- Add timer to `ClientWidget_ITG` that polls question status
- Show "Download All Layers (ZIP)" button when completed
- Call `GET /api/question/{id}/layers/download`

---

## ⚖️ Key Decisions

### Decision 1: Skip mid-level Z-ordering (for now)

The design doc says mid-level Bosses should wait for ALL children, then Z-order them. `itg_node.py` doesn't do this — it creates children and immediately marks itself complete.

**Plan:** Top Boss (depth 0) collects ALL leaf results at the end, does one final Z-ordering + combine. This is simpler and works for depth ≤ 2.

Mid-level Z-ordering can be added later.

### Decision 2: Shared ComfyUI, serialized splits

Only ONE ComfyUI instance per machine. ITG splits are serialized — if a split is already running, new tasks wait. Add "ComfyUI busy" status to GUI.

### Decision 3: Boss creates root task via batch endpoint

No new endpoint needed. Boss detects pending question → creates depth=0 task via `POST /api/tasks/batch` → claims it immediately.

### Decision 4: Same QThread class for Boss and Worker

Both Boss and Worker do the EXACT same thing (split 1→2, judge). The only difference is what they do AFTER:
- Boss (depth < max_depth): creates children
- Worker (depth ≥ max_depth): uploads final result

`ITGSplitThread` handles only the split+judge. Post-split logic stays in the GUI main thread.

---

## 🔢 Files to Modify

| File | Changes |
|------|---------|
| `src/gui.py` | +ITGSplitThread class, rewrite Boss/Worker ITG stubs, add previews + progress + auto-pilot |
| `src/app.py` | Possibly add `/api/question/{id}/start_root` endpoint (or use existing batch) |
| No new files | All changes in existing gui.py |

---

## 🧪 What the Test Will Look Like After Building

```
Nir clicks:
  1. Desktop Client tab → Upload image → Submit
  2. Laptop Boss tab → Auto-Pilot ✅ → watches root split happen
  3. Laptop Worker tab → Polling → Auto-Claim ✅ → watches layers split
  4. Desktop Worker tab → Polling → Auto-Claim ✅ → watches layers split
  5. Laptop Boss → when all done → Arrange Z-Order → Upload Final 6
  6. Desktop Client → Refresh → Download ZIP ✅
```

---

*Ready for Desktop AI review.*
