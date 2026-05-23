# 🔍 AUTO-PILOT DESIGN REVIEW — Desktop AI

**Reviewer:** Desktop AI | **Date:** May 23, 2026 | **Verdict:** ✅ APPROVED WITH NOTES

---

## Overall Assessment

The plan is **solid**. The architecture is already designed for this — the Boss/Worker polling loop was envisioned in DESIGN.md and prototyped in TEXT_TO_GHOST_DESIGN.md. This is a natural, low-risk evolution. ~95 lines of GUI code, zero API changes, fully backward-compatible.

**Recommended for implementation** after addressing the 7 findings below.

---

## Finding #1 — 🟡 Minor: Wrong filename reference

**Location:** AUTOPILOT_DESIGN.md §2

The plan references `TTG_DESIGN.md` §5.2 and §6.1. This file does not exist. The correct file is `TEXT_TO_GHOST_DESIGN.md`, which DOES contain §5.2 (`boss_loop`) and §6.1 (`worker_loop`) at lines 236-362. Fix the reference before merging.

---

## Finding #2 — 🟡 Minor: ITG auto-gen depends on stub methods

**Location:** AUTOPILOT_DESIGN.md §3.3 | Code: `gui.py:1425-1433`

`WorkerWidget_ITG.split_task()` and `upload_results()` are **stubs** that print placeholder messages like _"use src/itg_node.py terminal interface. GUI split coming."_ They don't actually do anything.

The plan says to wire auto-gen for ITG but the chain `poll → claim → split → upload` can't work because `split_task()` and `upload_results()` are unimplemented. Either implement these methods first, or defer ITG auto-gen to a separate PR.

---

## Finding #3 — 🔴 CRITICAL: claim_task() API is click-only

**Location:** `gui.py:925` → `claim_task(self, item)` | Plan: §3.2

`claim_task()` takes a **QListWidgetItem**, not a task dict:

```python
def claim_task(self, item):
    t = item.data(Qt.ItemDataRole.UserRole)  # ← must be a QListWidgetItem
```

The auto-gen loop needs to call `claim_task()` programmatically, but there's no way to pass raw task data. Options:

1. **Refactor `claim_task()`** to accept an optional `task_dict` parameter (recommended):
   ```python
   def claim_task(self, item=None, task_dict=None):
       t = task_dict if task_dict else item.data(Qt.ItemDataRole.UserRole)
   ```
2. Populate `self.tasks_list` then programmatically select + trigger, but this is fragile.

Without this fix, the auto-gen loop can "see" tasks via `poll_tasks()` but can't claim them automatically.

---

## Finding #4 — 🟡 Medium: upload_result() doesn't trigger next poll

**Location:** `gui.py:1005-1028` | Plan: §3.2

After successful upload, `upload_result()` clears state (active_task=None, generated_path=None) but **does not call `poll_tasks()`**. The plan says "after upload succeeds → loop back to step 1" — this needs either:

- Add `self.poll_tasks()` at line ~1019 (after successful state reset)
- OR let the existing poll timer catch it on the next tick (5s delay)

The simpler approach: add `if self.auto_gen_cb.isChecked(): self.poll_tasks()` after upload success. This avoids waiting 5s for the poll timer.

---

## Finding #5 — 🔴 EXISTING BUG: generate_image() uses formatted text as prompt

**Location:** `gui.py:960-961` | Affects: Plan §3.2 auto-gen

```python
prompt = self.active_task_label.toPlainText().strip() or self.active_task["prompt"]
```

`active_task_label` contains formatted text from `claim_task()` (line 934):
```
"Task #201 -- Layer 1\nPrompt: the actual prompt..."
```

`toPlainText()` returns the full formatted string including line breaks and "Task #..." prefix. This goes directly into Qwen's prompt. **This is a garbage prompt** — Qwen gets "Task #201 -- Layer 1\nPrompt: polar bears charging..." instead of just the prompt.

For manual mode, the user probably overwrites `active_task_label` before clicking Generate. For auto-gen, there's no human to fix it — this WILL produce broken images.

**Fix:**
```python
prompt = self.active_task["prompt"]  # always use the real prompt
```

This is an EXISTING bug, not caused by the plan, but it blocks auto-gen reliability.

---

## Finding #6 — 🟢 Nit: Race condition on double split

**Location:** Plan §3.1 | API: `app.py:179`

If two Boss instances poll simultaneously, both could try to split the same PENDING question. The API allows splitting on both PENDING and PROCESSING statuses (line 179). The plan's `_splitting_now` flag protects within one instance, but not across instances.

**Mitigation:** In practice, a single DM machine runs one Boss. For Stage 2+ with redundant Bosses, server-side dedup should be added. Not a blocker for now.

---

## Finding #7 — 🟢 Nit: Plan says "Mark question as in-progress" — already handled

**Location:** Plan §3.1 | API: `app.py:194-195`

The plan suggests the auto-pilot needs to mark questions as in-progress, but the **API already does this**: after split, question status changes from PENDING → PROCESSING (line 194). The auto-pilot just needs to filter for `status == "pending"` when polling, which prevents re-splitting already-split questions. No extra work needed.

---

## Finding #8 — 🟡 Minor: TTG_DESIGN.md missing from GitHub

The file referenced in §2 of the plan returns 404 on GitHub. The correct filename is `TEXT_TO_GHOST_DESIGN.md`. Either rename it to `TTG_DESIGN.md` for consistency with `ITG` naming, or fix the reference in the AUTOPILOT plan.

---

## Summary

| # | Severity | Item | Blocking? |
|---|----------|------|-----------|
| 1 | 🟡 Minor | Wrong filename reference | No |
| 2 | 🟡 Minor | ITG auto-gen stubs | No (defer ITG) |
| 3 | 🔴 Critical | claim_task() click-only API | **Yes** |
| 4 | 🟡 Medium | upload doesn't trigger next poll | **Yes for flow** |
| 5 | 🔴 Existing Bug | generate_image bad prompt | **Yes** |
| 6 | 🟢 Nit | Race condition (unlikely) | No |
| 7 | 🟢 Nit | Duplicate "in-progress" logic | No |
| 8 | 🟡 Minor | Wrong filename on GitHub | No |

**Blockers to fix before/while implementing:**
1. Fix `claim_task()` to accept optional task_dict
2. Fix `generate_image()` prompt construction
3. Add poll trigger after upload success
4. Fix filename references (TTG_DESIGN.md → TEXT_TO_GHOST_DESIGN.md)

**Optional:** Defer ITG auto-gen (Step 3) until split_task + upload_results are implemented.

**Verdict:** ✅ Ship it — just fix findings #3, #4, and #5 while implementing. The plan is a natural, well-scoped evolution of existing infrastructure.

---

*End of review.*
