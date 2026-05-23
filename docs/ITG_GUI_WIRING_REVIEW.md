# 🔍 ITG GUI Wiring Plan — Desktop AI Review

**Reviewed by:** Desktop AI | **Date:** May 23, 2026 | **Verdict:** APPROVED with changes ✅

---

## ✅ AGREEMENTS — Plan is solid on all of these:

1. **3-phase approach** — correct ordering: Worker (Phase 1) → Boss (Phase 2) → Combine + Client (Phase 3). Worker first because it's simpler and validates the thread architecture.

2. **One `ITGSplitThread` for both Boss and Worker** — `itg_node.py` confirms both roles do the exact same split+judge. Thread reuse is the right call.

3. **Shared ComfyUI, serialized splits** — only one ComfyUI instance per machine. `itg_splitter.py` already has `TIME_BETWEEN_CALLS = 1.0` throttling. Add "ComfyUI busy" status to GUI.

4. **Skip mid-level Z-ordering** — matches current `itg_node.py` behavior. Only Top Boss (depth 0) does final Z-order + combine. Mid-level nodes just split → create children → mark complete.

5. **No new files** — all changes in `gui.py`. The backend code (`itg_node.py`, `itg_splitter.py`, `itg_judge.py`, `itg_combine.py`) is correct and doesn't need modification (except the bug below).

6. **Phase 3 Client auto-poll sequenced last** — correct. Client submission already works. Adding auto-poll for download after Phases 1-2 are done is the right order.

---

## 🔴 CRITICAL FIX #1: Thread MUST handle garbage retry loop

**The problem:** The plan says `ITGSplitThread` handles only "split+judge" with "post-split logic stays in the GUI main thread." But the garbage retry loop in `itg_node.py` (lines 119-140) **re-runs ComfyUI** — a 25s to 10-minute blocking operation that generates new images with different seeds.

You cannot split retry logic across the thread/main boundary. Starting a new thread from the main thread for each retry would be messy and racy.

**The fix:** `ITGSplitThread.run()` must handle the FULL retry flow internally:

```python
# Inside ITGSplitThread.run()
max_retries = 3
for attempt in range(max_retries):
    # Split with different seed per attempt
    layer_files = split_image_into_n_layers(input_path, ...)

    # Judge
    good_layers, garbage = judge_all(layer_files)

    if good_layers:
        break  # success!
    elif attempt < max_retries - 1:
        self.progress_signal.emit(f"All garbage — retrying (attempt {attempt+2}/{max_retries})...")
        continue
    else:
        self.error_signal.emit("3 dual-garbage retries exhausted")
        return
```

The thread emits `finished_signal(good_layers, judgments)` when done. The GUI main thread only creates children or marks complete based on the result — never starts new threads for retries.

---

## 🔴 CRITICAL FIX #2: Thread scope — handle FULL node iteration

**The problem:** The plan says thread does "split+judge only." But `itg_node.py`'s `claim_and_process()` flow (lines 56-199) is:

```
download_input → split → judge → [retry if garbage] → upload → generate_child_prompts → create_children
```

The plan omits:
- **Upload** (HTTP POST, fast but should be in thread for consistency)
- **Child prompt generation** (`_generate_child_prompt()` calls Ollama — 5-10s blocking)

**The fix:** Thread handles everything up to and including result upload. Returns a result object:

```python
class ITGSplitResult:
    good_layer_paths: list[str]
    uploaded_filenames: list[str]
    descriptions: list[str]       # from judge_layer_quality()
    finish_type: str              # "children" or "final" or "failed"
```

Post-thread logic in main thread:
- If `finish_type == "children"`: create child tasks via API (fast HTTP)
- If `finish_type == "final"`: upload final results to task endpoint (fast HTTP)
- If `finish_type == "failed"`: reset task or retry

This avoids blocking the UI during child prompt generation and keeps the thread/main boundary clean.

---

## 🟡 CONCERN #1: Bug in itg_node.py — duplicate Ollama calls

**The bug:** `itg_node.py` line 177 calls `_generate_child_prompt()` which re-calls `judge_layer_quality()` at line 209. But the layer was ALREADY judged at line 110-113, which returned a `description` field. This doubles Ollama calls per good layer (2 extra calls for 2 good layers = ~10-20s wasted).

**The fix:** Pass the existing description to child prompt generation:

```python
# In claim_and_process(), line 109-116:
judgments = []
for i, lf in enumerate(layer_files):
    judgment = judge_layer_quality(lf, ...)
    judgments.append(judgment)
    # ...

# Later, when creating children (line 175-177):
for i, (lf, fn, judgment) in enumerate(zip(good_layers, uploaded_filenames, good_judgments)):
    child_prompt = f"Decompose this layer further: {judgment['description']}"
    # ...instead of calling _generate_child_prompt() which re-judges
```

This should be fixed BEFORE wiring the GUI, since the thread will need to call this code.

---

## 🟡 CONCERN #2: Worker UI — auto-pilot vs manual

**The plan shows:** Worker with two separate buttons (Split → Upload). This works for manual mode but not for auto-pilot.

**The fix:** Add an "Auto-Process" checkbox (mirroring TTG Worker's "Auto-Generate"):
- When checked: after claiming a task → automatically process (split→judge→upload) → poll next
- When unchecked: manual mode with two-button flow (Split → Upload)
- Both modes use the same `ITGSplitThread` under the hood

The current `WorkerWidget_ITG` already has polling and claim — just needs the auto-process flag.

---

## 🟡 CONCERN #3: Boss auto-pilot needs state machine

**The plan says:** Boss auto-pilot "mirrors TTG Boss pattern." But TTG Boss only creates tasks (fast). ITG Boss also processes the root task (slow) and then must wait for children.

**The fix:** Boss auto-pilot needs a state machine:

```
POLLING → PROCESSING_ROOT → WAITING_CHILDREN → COMBINING → DONE
```

- **POLLING:** Poll for pending ITG questions every 3s. Found one? → PROCESSING_ROOT
- **PROCESSING_ROOT:** Create root task → claim → run ITGSplitThread → create children → WAITING_CHILDREN
- **WAITING_CHILDREN:** Poll task status. All children complete? → COMBINING
- **COMBINING:** Download all child results → `determine_z_order()` → `reduce_to_6_layers()` → upload complete → DONE
- **DONE:** Mark question complete. Back to POLLING for next question.

The GUI should show the current state prominently.

---

## 🟢 NITPICKS:

### N1: ComfyUI config already exists
The `BossWidget_ITG` and `WorkerWidget_ITG` already have ComfyUI URL fields, Test buttons, and Vision model dropdowns (`qwen3-vl:4b`, `qwen3-vl:8b`). The plan frames these as new UI — they're already there. Just acknowledge and reuse.

### N2: Client ITG tab already works
`ClientWidget_ITG` uploads images, creates questions, displays question list. Phase 3 only needs to add an auto-poll timer + Download ZIP button. ✅

### N3: combine.py already handles edge cases
`itg_combine.py` correctly handles: N==6 (pass-through), N<6 (add empty layers), N>6 (pair-combine farthest). No changes needed.

---

## 📋 FINAL VERDICT

| Aspect | Verdict |
|--------|---------|
| Architecture | ✅ Correct |
| Phase ordering | ✅ Correct |
| Thread design | 🔴 Needs 2 scope fixes |
| itg_node.py | 🟡 1 bug to fix |
| Worker UX | 🟡 Auto-pilot needed |
| Boss UX | 🟡 State machine needed |
| ComfyUI config | 🟢 Already exists |
| Final combine | 🟢 No changes needed |

**Overall:** Plan is ~85% correct. Fix the 2 critical thread issues + 1 itg_node bug, then build. Approved. 👍
