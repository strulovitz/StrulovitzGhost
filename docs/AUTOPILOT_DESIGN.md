# 🤖 Auto-Pilot — One-Click Fully Automatic Pipeline

**Status:** Design | **Date:** May 23, 2026 | **Author:** Laptop AI

> This document specifies the changes needed to make StrulovitzGhost work as a
> **fully automatic** system — submit a scene and walk away. All 6 layers generated
> without any manual clicking. No new scripts. All changes inside the existing GUI.

---

## 1. The Vision

```
User pastes scene → clicks Submit → walks away ☕
          ↓
    Boss auto-detects → auto-splits with LLM → creates 6 tasks
          ↓
    Workers (Laptop + Desktop) auto-detect tasks → auto-claim → auto-generate → auto-upload
          ↓
    6 RGBA layers complete ✅
```

The architecture is ALREADY designed for this (see DESIGN.md Polling Mechanism,
TEXT_TO_GHOST_DESIGN.md §5.2 boss_loop, §6.1 worker_loop). The infrastructure exists —
we just need to wire the final automation into the GUI.

---

## 2. Current State — What's Manual

### Boss (BossWidget_TTG in gui.py)
| Action | Manual? | How |
|--------|---------|-----|
| Detect new questions | ✅ Manual | Click "Refresh" |
| Auto-split with LLM | ✅ Manual | Click "Auto-Split with LLM" |
| No poll timer | ❌ Missing | Boss has no auto-loop |

### Worker (WorkerWidget_TTG in gui.py)
| Action | Manual? | How |
|--------|---------|-----|
| Poll for tasks | 🔄 Auto | Poll timer every 5s |
| Claim task | ✅ Manual | Click task in list → calls claim_task() |
| Edit negative prompt | ✅ Manual | User edits before generate |
| Generate image | ✅ Manual | Click "Generate with Qwen AI" |
| Upload result | ✅ Manual | Click "Upload Result PNG" |

### Worker (WorkerWidget_ITG in gui.py)
| Action | Manual? | How |
|--------|---------|-----|
| Poll for tasks | 🔄 Auto | Poll timer every 5s |
| Claim/process | ✅ Manual | User clicks to claim + process |

---

## 3. Changes Required

### 3.1 BossWidget_TTG — Auto-Pilot Polling

**Add a poll timer** that runs every 3 seconds. On each tick:

```
poll_boss():
  1. GET /api/questions?type=TTG → check for NEW pending questions
  2. If pending question found AND not already processing one:
     a. Run auto_split() on that question
     b. Mark question as "in-progress" to avoid re-splitting
  3. If currently splitting a question, skip (wait for it to finish)
```

**Add "Auto-Pilot" checkbox** in the Boss UI. When checked:
- Starts the poll timer
- Label changes: "Auto-Pilot ON — watching for new scenes..."
- Any new pending TTG question is auto-split immediately

**Edge cases:**
- If LLM is not available, show error and keep polling (will retry)
- If split fails, mark question, don't retry same question
- Multiple questions pending → process oldest first

### 3.2 WorkerWidget_TTG — Auto-Generate Loop

**Add "Auto-Generate" checkbox** in the Worker UI. When checked AND polling is active:

```
poll_tasks_auto():
  1. GET /api/tasks?status=pending&type=TTG
  2. If tasks found AND no active task:
     a. claim_task() on the first task
     b. After claim succeeds → generate_image()
     c. After generation finishes → upload_result()
     d. After upload succeeds → loop back to step 1
  3. If no tasks found → wait for next poll
  4. If generation fails → reset task, wait for next poll
```

**The chain:** `poll → claim → generate → upload → poll → ...`

All three methods (`claim_task`, `generate_image`, `upload_result`) already exist.
We just need to chain them together automatically.

**Neg prompt handling:** When auto-generating, use the negative prompt from the task
as-is. The user doesn't get to edit it. This is fine for auto mode.

### 3.3 WorkerWidget_ITG — Auto-Generate Loop (Bonus)

Same pattern as TTG Worker. When "Auto-Generate" checked:
- Auto-claim ITG tasks
- Auto-process them
- Auto-upload results

---

## 4. UI Changes

### Boss Tab (new checkbox row)
```
┌──────────────────────────────────────────────────┐
│  [✔] Auto-Pilot  |  Status: Watching for scenes  │
│                                                   │
│  Incoming Questions:                              │
│  #42 | D&D Night Camp | [split in progress...]    │
│  Layer Tasks: (#42)                               │
│  Layer 1: [completed] ...                         │
└──────────────────────────────────────────────────┘
```

### Worker Tab — TTG (new checkbox)
```
┌──────────────────────────────────────────────────┐
│  Worker ID: [laptop-5090]  Method: [diffusers ▼]  │
│  [Start Polling]  [✔] Auto-Generate              │
│                                                   │
│  Status: Claimed Task #201 → Generating → 67%    │
│  Status: Uploaded Layer 1! Polling for next...    │
└──────────────────────────────────────────────────┘
```

### Worker Tab — ITG (new checkbox)
```
┌──────────────────────────────────────────────────┐
│  Worker ID: [laptop-5090]                        │
│  [Start Polling]  [✔] Auto-Generate              │
│                                                   │
│  Status: Processing task #301 → Done!             │
└──────────────────────────────────────────────────┘
```

---

## 5. Implementation Plan

### Step 1: BossWidget_TTG auto-pilot (~30 lines)
- Add `self.auto_pilot_cb` (QCheckBox)
- Add `self.boss_poll_timer` (QTimer, 3s interval)
- `_boss_poll()` method: checks pending questions, auto-splits
- Track `_splitting_now` flag to prevent double-split
- Wire checkbox to start/stop timer

### Step 2: WorkerWidget_TTG auto-generate (~40 lines)
- Add `self.auto_gen_cb` (QCheckBox)
- Modify `poll_tasks()` to check if auto-gen is enabled
- If auto-gen + tasks available + no active task → auto-claim
- In `on_gen_finished()`: if auto-gen → auto-upload
- In `upload_result()`: after success, if auto-gen → trigger next poll immediately
- Add auto-gen loop continuation logic

### Step 3: WorkerWidget_ITG auto-generate (~25 lines)
- Same pattern as TTG Worker
- Add checkbox, modify poll_tasks, chain claim→process→upload

### Step 4: Test locally
- Start Flask server
- Open GUI with all 3 modes
- Submit scene → Boss auto-splits → Worker auto-generates → all layers complete

### Step 5: Push to GitHub + coordinate with Desktop
- Desktop pulls, runs Worker with auto-gen + server URL pointing at Laptop
- Full LAN test

---

## 6. Error Handling

| Scenario | Behavior |
|----------|----------|
| LLM unavailable during auto-split | Log error, keep polling, retry next tick |
| Split returns empty | Log error, skip question, don't retry |
| Claim fails (task already taken) | Skip, try next task |
| Generation fails (GPU OOM, etc.) | Reset task via API, log error, continue polling |
| Upload fails | Log error, keep generated file, try re-uploading |
| Server unreachable | Log error, keep polling (will reconnect) |
| No tasks available | Sleep, poll again |

---

## 7. What Does NOT Change

- Flask API endpoints — zero changes
- models.py — zero changes
- generator.py — zero changes
- llm.py — zero changes
- scene_viewer.py — zero changes
- All existing manual workflows still work (checkbox OFF = manual mode)
- Backward compatible — existing behavior preserved

---

## 8. LAN Test Scenario (After Implementation)

### Setup
```
Laptop (10.0.0.6):
  1. Start Flask server: python app.py
  2. Start GUI: python gui.py
  3. Boss tab: Auto-Pilot ON
  4. Worker tab: Start Polling + Auto-Generate ON

Desktop (10.0.0.x):
  1. Start GUI: python gui.py
  2. Set Server URL: http://10.0.0.6:5000
  3. Worker tab: Start Polling + Auto-Generate ON
```

### Execute
```
Laptop Client tab:
  Paste Silver Warrior scene → click Submit → DONE
```

### Expected
```
1. Boss auto-detects → splits into 6 layers (~30s)
2. Laptop Worker auto-claims Layer 1 → generates (~4-5 min on 5090)
3. Desktop Worker auto-claims Layer 2 → generates (~9 min on 4070 Ti)
4. Both Workers continue claiming + generating until all 6 done
5. All 6 RGBA layers in src/output/ttg/final/
6. Database shows question "completed" ✅
```

---

*End of AUTOPILOT_DESIGN.md*
