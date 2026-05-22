# 🧠 Text To Ghost (TTG) — Detailed Design Document

**Status:** Planning | **Date:** May 22, 2026 | **Author:** Laptop AI

> This document is a detailed software design for the TTG mode.
> Read alongside: [NIR_VISION_MAY_22.md](NIR_VISION_MAY_22.md), [IMAGE_TO_GHOST_DESIGN.md](IMAGE_TO_GHOST_DESIGN.md)

---

## 1. Overview

**Text To Ghost** converts a natural language scene description into 6 RGBA image layers
for physical Pepper's Ghost display. It uses a **recursive hierarchical architecture**
where bosses split text and workers generate images — in parallel, on multiple machines.

### 1.1 Core Philosophy

| Role | Does | Uses |
|------|------|------|
| **Client** | Submits scene description | Just writes text |
| **Boss** | Splits text into sub-tasks, combines results | Qwen LLM (Ollama/LM-Studio) |
| **Worker** | Generates one image per sub-task | Qwen-Image-2512 (ComfyUI or diffusers) |

**Bosses never touch images** (except final combining). **Workers never touch text** (except receiving their prompt).

---

## 2. Architecture

### 2.1 Three Entities, One Website, One App

```
┌─────────────────────────────────────────────────────┐
│                  FLASK WEBSITE                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Questions │  │  Tasks   │  │  Image Files     │  │
│  │ (SQLite)  │  │ (SQLite) │  │ (filesystem)     │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│  REST API: /api/questions, /api/tasks, /api/files   │
└────────┬────────────────┬────────────────┬─────────┘
         │                │                │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ CLIENT  │      │  BOSS   │      │ WORKER  │
    │ (submit)│      │ (split) │      │ (draw)  │
    └─────────┘      └─────────┘      └─────────┘
```

All three user types are tabs/modes in the **same PyQt6 application**.
The website (Flask) runs separately — it's the central hub.

### 2.2 Recursive Hierarchy

```
                    MANAGER (Boss Level 2)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    TEACHER #1      TEACHER #2      TEACHER #N
    (Boss Lvl 1)    (Boss Lvl 1)    (Boss Lvl 1)
         │               │               │
    ┌────┼────┐     ┌────┼────┐     ┌────┼────┐
    ▼    ▼    ▼     ▼    ▼    ▼     ▼    ▼    ▼
   W1   W2   WN    W1   W2   WN    W1   W2   WN
  (Workers — actual GPU work)
```

- **Manager** splits the SCENE into 6 TEACHER-tasks
- **Each Teacher** splits one TEACHER-task into 6 STUDENT-tasks
- **Each Worker (Student)** generates ONE image for ONE tiny sub-prompt
- On the way BACK up: Teachers combine 6 student images → Manager combines 6 teacher images
- Final output: exactly 6 RGBA layers for physical display

### 2.3 Data Flow (Complete Lifecycle)

```
Step 1: Client → Website
  POST /api/questions  { type: "TTG", text: "Night camp..." }

Step 2: Boss (Manager) → Website (polling)
  GET /api/questions/pending
  GET /api/questions/42  → sees new question

Step 3: Boss (Manager) → LLM → Website
  Splits text into 6 layer descriptions using Qwen LLM
  POST /api/tasks (×6)  { question_id: 42, depth: 0, parent_task_id: null, prompt: "...", layer_number: 1..6 }

Step 4: Boss (Teacher) → Website (polling)
  GET /api/tasks/pending?type=TTG
  Claims task 101 (layer 3 of 6 from Manager)
  POST /api/tasks/101/claim  { worker_id: "teacher_1" }

Step 5: Boss (Teacher) → LLM → Website
  Splits task 101's prompt into 6 sub-prompts
  POST /api/tasks (×6)  { question_id: 42, depth: 1, parent_task_id: 101, prompt: "..." }

Step 6: Worker → Website (polling)
  GET /api/tasks/pending?type=TTG
  Claims task 201
  POST /api/tasks/201/claim  { worker_id: "student_5" }

Step 7: Worker → GPU → Website
  Generates image using Qwen-Image-2512 (prompt from task 201)
  POST /api/tasks/201/result  (multipart: generated PNG)

Step 8: Boss (Teacher) → Website (polling)
  Sees task 201-206 all complete
  Downloads 6 images from Website: GET /api/files/task_42_03_01.png etc.
  PIL alpha_composite: combines all 6 → one classroom image
  POST /api/tasks/101/result  (multipart: combined PNG)

Step 9: Boss (Manager) → Website (polling)
  Sees task 101-106 all complete (all 6 teachers done)
  Downloads 6 images from Website
  PIL alpha_composite: combines → final 6-layer scene
  POST /api/questions/42/complete  (multipart: 6 final PNGs)

Step 10: Client → Website
  Polls: GET /api/questions/42  → sees status "completed"
  Downloads: GET /api/files/final_layer_1.png through _6.png
  Displays on physical Pepper's Ghost setup

DONE.
```

---

## 3. Database Schema

### 3.1 Questions Table (Modified)

```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL DEFAULT 'TTG',      -- 'TTG' or 'ITG'
    text TEXT NOT NULL,                     -- Scene description (TTG) or image path/URL (ITG)
    style TEXT DEFAULT 'Ghibli animation',  -- Global style
    max_depth INTEGER DEFAULT 0,            -- 0 = no hierarchy (flat: 1 boss, 6 workers)
    status TEXT DEFAULT 'pending',          -- pending, processing, completed, failed
    global_negative_prompt TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
```

### 3.2 Tasks Table (Modified)

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    type TEXT NOT NULL DEFAULT 'TTG',       -- 'TTG' or 'ITG'
    parent_task_id INTEGER,                 -- NULL for root tasks, FK to self for children
    depth INTEGER DEFAULT 0,                -- 0 = root, 1 = children, 2 = grandchildren...
    max_depth INTEGER DEFAULT 0,            -- When to stop recursing (set by Boss)
    layer_number INTEGER,                   -- 1-6 within this parent's set
    prompt TEXT NOT NULL,                   -- What to generate/draw
    negative_prompt TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',          -- pending, claimed, completed, failed
    worker_id TEXT,                         -- Who claimed it
    result_filename TEXT,                   -- Path to generated image on website disk
    claim_time DATETIME,
    complete_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id),
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);
```

### 3.3 Key Design Decisions

| Decision | Reason |
|----------|--------|
| `type` on BOTH tables | Simplifies queries: `WHERE type='TTG'` without joining |
| `parent_task_id` self-referencing | Natural tree structure, unlimited depth |
| `depth` denormalized | Avoid recursive CTEs for common queries like "find all leaf tasks" |
| `max_depth` on task | Each boss knows when to stop creating children |
| NO image blobs | Files on disk, only paths in DB |
| `result_filename` = path | Matches naming convention: `task_{id}.png`, `task_{id}_01.png` etc. |

---

## 4. Flask API Endpoints

### 4.1 Existing (Keep As-Is, Add `type` Filter)

| Method | Endpoint | Purpose | Change |
|--------|----------|---------|--------|
| POST | `/api/questions` | Client submits scene | Add `type: "TTG"` |
| GET | `/api/questions` | List all questions | Add `?type=TTG` filter |
| GET | `/api/questions/<id>` | Get question + its tasks | No change |
| PUT | `/api/questions/<id>` | Client cancels | No change |
| POST | `/api/questions/<id>/complete` | Boss uploads final 6 layers | No change |
| GET | `/api/tasks/pending` | Workers poll | Add `?type=TTG` filter |
| POST | `/api/tasks/<id>/claim` | Worker claims task | No change |
| POST | `/api/tasks/<id>/result` | Worker uploads result | No change |
| PUT | `/api/tasks/<id>` | Boss edits prompt/negative | No change |
| POST | `/api/tasks/<id>/reset` | Return failed task to queue | No change |

### 4.2 New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/tasks/batch` | Boss creates multiple child tasks at once (atomic) |
| GET | `/api/tasks/<id>/children` | Get all child tasks of a parent |
| GET | `/api/tasks/<id>/children/status` | Summarized status of children (how many pending/claimed/complete) |
| GET | `/api/files/<filename>` | Download any image file from website disk |
| DELETE | `/api/questions/<id>/cleanup` | Delete intermediate files, keep only final 6 layers |
| GET | `/api/health` | Returns server status, disk space, active question count |

### 4.3 File Serving

Files live in `src/output/ttg/` on the website's disk:
- `src/output/ttg/task_42_input.txt` — original prompt (for debugging)
- `src/output/ttg/task_42_01.png` — intermediate worker result
- `src/output/ttg/final/task_42_layer_1.png` through `task_42_layer_6.png` — final 6 layers

`GET /api/files/<filename>` serves them with proper content-type.

---

## 5. Boss Logic (The Brain)

### 5.1 Flat Mode (max_depth = 0, the current architecture)

```
1. Boss polls: GET /api/questions/pending?type=TTG
2. Sees new question #42: "D&D night camp..."
3. Sends to Qwen LLM via llm.py → gets 6 layer prompts back
4. Creates 6 tasks: POST /api/tasks (×6)
   { question_id: 42, type: "TTG", depth: 0, max_depth: 0, prompt: "...", layer_number: 1..6 }
5. Polls: GET /api/questions/42 → checks task statuses
6. All 6 complete → downloads images → combines (if needed) → uploads final
   POST /api/questions/42/complete
```

### 5.2 Hierarchical Mode (max_depth > 0, the NEW recursive architecture)

```python
def boss_loop(self):
    while True:
        # 1. Check for new jobs
        pending = GET /api/questions/pending?type=TTG
        for question in pending:
            self.handle_new_question(question)

        # 2. Check our active jobs — any children complete?
        for question in self.active_questions:
            tasks = GET /api/questions/{question.id}
            completed_children = [t for t in tasks if t.depth == question.current_depth
                                  and t.status == 'completed'
                                  and t.parent_task_id in self.our_tasks]

            for parent_task in self.our_tasks:
                children = GET /api/tasks/{parent_task.id}/children
                if all(c.status == 'completed' for c in children):
                    self.handle_children_done(parent_task, children)

        time.sleep(2)

def handle_new_question(self, question):
    """Receive a new scene description. Split it into layer tasks."""
    layers = llm.split_scene(question.text, question.style, question.max_depth)
    parent_tasks = []
    for i, layer in enumerate(layers):
        task = POST /api/tasks {
            question_id: question.id,
            type: "TTG",
            depth: 0,
            max_depth: question.max_depth,
            parent_task_id: None,
            prompt: layer['prompt'],
            negative_prompt: layer['negative_prompt'],
            layer_number: i + 1
        }
        parent_tasks.append(task)
    self.our_tasks = parent_tasks
    self.active_questions.append(question)

def handle_children_done(self, parent_task, children):
    """All children of a parent_task are complete. Combine and upload."""
    if parent_task.depth < parent_task.max_depth:
        # This boss is a MIDDLE boss → create grand-children
        # Wait — in TTG, only the LOWEST boss does combining.
        # Actually: EVERY boss at every level creates children.
        # The children are ALWAYS workers (they generate).
        # The boss only combines when his OWN children are done.
        # The combined result goes UP to be his parent's child result.
        pass

    # Download children's images
    images = []
    for child in sorted(children, key=lambda c: c.layer_number):
        img = download_image(child.result_filename)
        images.append(img)

    # Combine mechanically
    combined = combine_layers(images, parent_task.layer_number)

    # Upload combined result
    filename = f"task_{parent_task.id}.png"
    save_image(combined, filename)
    POST /api/tasks/{parent_task.id}/result  (upload combined PNG)
```

### 5.3 The Splitting Algorithm (Qwen LLM)

The Boss uses `llm.py` with a hierarchical-aware template:

```python
SPLIT_PROMPT_HIERARCHICAL = """You are a scene splitter for StrulovitzGhost.

Your job: take a scene description and split it into exactly {count} sub-descriptions.

Current depth: {depth} of {max_depth}
Layer number: {layer_number} of 6

If depth == max_depth (you are at the bottom):
  Split into TINY details — individual objects, not scenes.
  Example: "a bouquet of flowers" → "one red rose, front view", "one yellow tulip, side view", etc.
  Each sub-description must be SMALL and SPECIFIC.

If depth < max_depth (you are a middle boss):
  Split into BROAD regions or character groups.
  Example: "night sky" → "moon", "stars", "clouds", etc.

Output ONLY valid JSON:
{
  "layers": [
    {"prompt": "...", "negative_prompt": "..."},
    ...
  ]
}

Style: {style}
Scene: {scene}"""
```

### 5.4 The Combining Algorithm (PIL mechanical)

```python
def combine_worker_results(image_paths, output_path):
    """Stack RGBA PNGs back-to-front. Bottom path = farthest layer."""
    # Images come sorted by sub-layer_number
    composite = Image.open(image_paths[0]).convert("RGBA")
    for path in image_paths[1:]:
        overlay = Image.open(path).convert("RGBA")
        composite = Image.alpha_composite(composite, overlay)
    composite.save(output_path, "PNG")
```

**Important:** The combined result becomes ONE image that the parent treats as a single layer.
The parent does NOT further split this combined result. The parent mechanically combines
6 combined results from his 6 children.

---

## 6. Worker Logic

### 6.1 Polling Loop

```python
def worker_loop(self):
    while True:
        tasks = GET /api/tasks/pending?type=TTG
        if not tasks:
            time.sleep(2)
            continue

        task = tasks[0]  # Take the first available

        # Claim it
        r = POST /api/tasks/{task.id}/claim  { worker_id: self.worker_id }
        if not r.ok:
            continue  # Someone else grabbed it

        # Generate
        self.generate(task)

def generate(self, task):
    """Generate one image from a prompt."""
    # Build the full green-screen prompt
    full_prompt = (
        f"{task['prompt']}. Completely solid, uniform flat chroma key "
        f"green color, hex #00FF00. No shadows, no gradients."
    )

    # Use Qwen-Image-2512 via diffusers (reuse existing generator.py)
    temp_path = f"temp_{uuid4()}.png"
    generate_diffusers(
        prompt=full_prompt,
        output_path=temp_path,
        negative_prompt=task.get('negative_prompt', ''),
        width=768, height=576,
        num_steps=15,
        guidance_scale=4.0,
        remove_bg=True,  # Chroma-key to alpha
    )

    # Upload result
    filename = f"task_{task['id']}.png"
    with open(temp_path, 'rb') as f:
        POST /api/tasks/{task['id']}/result  files={'image': f}

    os.remove(temp_path)
```

### 6.2 Worker-Specific Notes

- Workers don't know or care about `depth`, `max_depth`, `parent_task_id`
- Workers don't know if they're a "student" or a "direct worker for the manager"
- Workers just: poll → claim → generate → upload → repeat
- ALL intelligence lives in the Boss. Workers are interchangeable.

---

## 7. GUI Design

### 7.1 PyQt6 Tab Structure

```
┌──────────────────────────────────────────────────┐
│  StrulovitzGhost 👻                    _ □ X     │
├──────────────────────────────────────────────────┤
│  [Text To Ghost]  [Image To Ghost]               │  ← QTabWidget
├──────────────────────────────────────────────────┤
│  I am: [ Client ▼ ]  [ Boss ▼ ]  [ Worker ▼ ]   │  ← Synchronized QComboBox
├──────────────────────────────────────────────────┤
│                                                   │
│         (Tab-specific content below)              │
│                                                   │
└──────────────────────────────────────────────────┘
```

The user-type dropdown is a single widget shared between both tabs (or synchronized via signal).

### 7.2 TTG Tab — Client View

```
┌──────────────────────────────────────────────────┐
│  Style: [ Ghibli animation          ▼ ]          │
│  Max Depth: [ 0  ▼ ]  (0 = flat, 1+ = hierarchy) │
│                                                   │
│  Scene Description:                               │
│  ┌─────────────────────────────────────────────┐  │
│  │  The group makes camp in a moonlit forest   │  │
│  │  clearing. An owl watches from a branch...  │  │
│  │                                             │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  Global Negative Prompt:                          │
│  ┌─────────────────────────────────────────────┐  │
│  │  watermark, signature, low quality          │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  [ Submit Scene ]                                 │
│                                                   │
│  ── Status ───────────────────────────────────── │
│  Question #42 | Status: completed ✅              │
│  [ Download Layer 1 ] [ Download Layer 2 ] ...   │
│  [ Download All (ZIP) ]                           │
└──────────────────────────────────────────────────┘
```

### 7.3 TTG Tab — Boss View

```
┌──────────────────────────────────────────────────┐
│  Boss ID: [ teacher_1               ]            │
│                                                   │
│  ── Pending Questions ────────────────────────── │
│  ┌────────────────────────────────────────────┐   │
│  │ #42 | D&D Night Camp    | pending | [Take] │   │
│  │ #43 | Dragon's Lair     | pending | [Take] │   │
│  └────────────────────────────────────────────┘   │
│                                                   │
│  ── Active Question #42 ──────────────────────── │
│  Depth: 0 | Max Depth: 2                         │
│                                                   │
│  My Tasks:                                        │
│  ┌────────────────────────────────────────────┐   │
│  │ Layer 1: "owl on branch..."    | ⏳ waiting │   │
│  │ Layer 2: "elf + human..."     | ✅ done     │   │
│  │ Layer 3: "dwarf + halfling..." | 🔧 working │   │
│  └────────────────────────────────────────────┘   │
│                                                   │
│  [Create Children (depth 1)]  [Combine & Upload]  │
│                                                   │
│  ── LLM Split Preview ────────────────────────── │
│  ┌────────────────────────────────────────────┐   │
│  │ (Shows the 6 prompts the LLM generated)    │   │
│  │ [Editable — can modify before creating]    │   │
│  └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### 7.4 TTG Tab — Worker View

```
┌──────────────────────────────────────────────────┐
│  Worker ID: [ student_05            ]            │
│  Method: [ diffusers ▼ ]                         │
│  Key Color: [ green ▼ ]                          │
│                                                   │
│  ── Available Tasks ──────────────────────────── │
│  ┌────────────────────────────────────────────┐   │
│  │ #201 | depth:2 | "One red rose..."  [Claim]│   │
│  │ #202 | depth:2 | "Yellow tulip..." [Claim] │   │
│  └────────────────────────────────────────────┘   │
│                                                   │
│  ── Active Task #201 ─────────────────────────── │
│  Prompt: "One red rose, front view..."            │
│  Negative: (editable)                             │
│  [ Generate ]                                     │
│  [████████████████░░░░] 67%                       │
│                                                   │
│  ── Preview ──────────────────────────────────── │
│  [Image preview after generation]                 │
│  [ Upload Result ]                                │
└──────────────────────────────────────────────────┘
```

---

## 8. File Storage & Cleanup

### 8.1 Directory Structure (on Website Computer)

```
src/output/
├── ttg/
│   ├── temp/              ← Intermediate worker results (cleaned up after job done)
│   │   ├── task_42_01.png
│   │   ├── task_42_01_01.png
│   │   └── ...
│   ├── final/             ← Final 6 layers (permanent, kept for Client download)
│   │   ├── task_42_layer_1.png
│   │   ├── task_42_layer_2.png
│   │   └── ...
│   └── logs/              ← Per-job log files
│       └── task_42.log
├── itg/
│   ├── temp/
│   ├── final/
│   └── logs/
└── combined/              ← Combined viewport (for debugging)
```

### 8.2 Cleanup Strategy

- **Immediately after upload:** Worker deletes local temp file (already done — line `os.remove(temp_path)`)
- **When Boss aggregates:** Boss downloads children's images, combines, uploads result — then POSTs `/api/questions/<id>/cleanup` which deletes all intermediate `/temp/` files for that question
- **When Client downloads:** Client gets final 6 layers from `/final/`. Files remain in `/final/` for N days (configurable), then auto-purged
- **Never leak disk space:** Every file created must have an owner task. When task completes, its temp files go. When question completes, ALL temp files go.

### 8.3 File Naming

```
task_{task_id}.png                          ← Worker result for this task
task_{task_id}.png                          ← Boss combined result for this parent task
final/task_{question_id}_layer_{1-6}.png    ← Final output for Client
```

The ancestry is tracked in the DB (`parent_task_id` chain), not in filenames.
The naming convention `task_42_01_02.png` is for ITG only (where each split inherits from parent).
In TTG, workers generate NEW images (not splits of a parent image), so ancestry in filenames is less meaningful.

---

## 9. Key Differences: TTG vs ITG

| Aspect | TTG | ITG |
|--------|-----|-----|
| Input | Text description | Image file (painting) |
| Boss work | Split TEXT with Qwen LLM | Split IMAGE with Qwen-Image-Layered |
| Worker work | Generate image from prompt (Qwen-Image-2512) | Split image into 2 layers (Qwen-Image-Layered) |
| Quality gate | None (text prompts always "good") | Qwen3-VL judges layer quality |
| Boss GPU needed? | NO (just LLM for text) | YES (Qwen-Image-Layered for splitting) |
| Workers = bosses? | NO (workers just draw) | YES (workers ARE bosses without children) |
| Combining | Boss mechanically combines children's images | Only TOP boss combines (pair from farthest) |
| File ancestry | Tracked in DB (parent_task_id chain) | Tracked in DB AND filename (task_42_01_02.png) |

---

## 10. Implementation Plan

### Phase 1: Database + API (Non-breaking)
1. Add `type`, `depth`, `max_depth`, `parent_task_id` to existing tables
2. Add new API endpoints (batch, children, files, cleanup, health)
3. Existing TTG flat mode still works (backward compatible)
4. Run existing 17 API tests — all must still pass

### Phase 2: GUI Tabs
1. Add QTabWidget with TTG and ITG tabs
2. Move existing TTG UI into TTG tab
3. Synchronize user-type dropdown between tabs
4. Add ITG tab (empty, just placeholder)

### Phase 3: Recursive Boss Logic
1. Implement hierarchical Boss loop (create children, monitor, combine)
2. Update LLM template for hierarchical mode
3. Test with flat mode (max_depth=0) — must work identically to current

### Phase 4: ITG Implementation
1. ComfyUI integration for Qwen-Image-Layered (layers=2)
2. Qwen3-VL quality judge integration
3. ITG Client/Boss/Worker views
4. ITG combining (pair from farthest)

### Phase 5: Testing
1. LAN test: Laptop (website + boss) + Desktop (worker)
2. Internet test: Desktop (website, Cloudflared) + Laptop (worker)

---

## 11. Open Questions

1. **Should the website do auto-cleanup?** Or should the Client/Boss explicitly call `/cleanup`?
2. **Concurrent questions?** Can one Boss handle multiple questions simultaneously?
3. **Worker failure recovery?** If a worker fails mid-generation, the task resets to pending (existing `/reset`). What about after N failures?
4. **LLM model selection?** Which Qwen model for hierarchical splitting? Current uses qwen3:14b.

---

*End of TEXT_TO_GHOST_DESIGN.md*
