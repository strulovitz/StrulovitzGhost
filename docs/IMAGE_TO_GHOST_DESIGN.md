# 🎨 Image To Ghost (ITG) — Detailed Design Document

**Status:** Planning | **Date:** May 22, 2026 | **Author:** Laptop AI

> This document is a detailed software design for the ITG mode.
> Read alongside: [NIR_VISION_MAY_22.md](NIR_VISION_MAY_22.md), [TEXT_TO_GHOST_DESIGN.md](TEXT_TO_GHOST_DESIGN.md)

---

## 1. Overview

**Image To Ghost** decomposes a single painting/artwork into 6 RGBA depth layers
for physical Pepper's Ghost display. It uses Qwen-Image-Layered to split images
and a recursive hierarchy where weak computers cooperate to achieve what one
strong computer can do.

### 1.1 Core Philosophy

| Role | Does | Uses |
|------|------|------|
| **Client** | Uploads painting | Just provides an image file |
| **Boss** | Splits image 1→2 layers, judges quality, passes good layers down, arranges Z-order on way up | Qwen-Image-Layered + Qwen3-VL |
| **Worker** | Same as Boss — splits 1→2, judges, uploads | Qwen-Image-Layered + Qwen3-VL |

**Workers ARE bosses without underlings.** Every node in ITG does the same work.
The difference is only position in the hierarchy.

### 1.2 Why "Messy" (vs TTG's "Clean")

Qwen-Image-Layered does NOT allow arbitrary per-layer control. You cannot give
one worker "the far half" and another "the close half." The model decides what
goes in which of the 2 output layers.

Therefore:
- **Every node must run Qwen-Image-Layered** (splitting IS the work)
- **Every node must run Qwen3-VL** (to judge if a layer is worth keeping)
- **Bosses do real GPU work** (not just thinking like in TTG)
- **On the way up: Z-order, don't combine** (only the top boss combines)

---

## 2. Architecture

### 2.1 The Split Tree

```
                    TOP BOSS (Manager)
                    Splits painting → 2 layers
                    Judges: Layer A ✓, Layer B ✓
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
        TEACHER #1                TEACHER #2
        Gets Layer A              Gets Layer B
        Splits → 2 layers         Splits → 2 layers
        Judge: ✓✓                 Judge: ✓✗ (one garbage, discarded)
            │                         │
      ┌─────┴─────┐                   │
      ▼           ▼                   ▼
   WORKER      WORKER              WORKER
   (bottom)    (bottom)            (bottom)
   Splits→2    Splits→2            Splits→2
   Judge: ✓✓   Judge: ✓✗           Judge: ✓✓

   Total good layers at bottom: 2 + 1 + 2 = 5

   ON THE WAY BACK UP:
   Teacher #1: Arranges 2 layers from his 2 workers by Z-depth
   Teacher #2: Arranges 1 layer from his 1 worker by Z-depth
   Top Boss: Arranges Teacher #1's layers + Teacher #2's layers = 3 layers total
   Top Boss: N=3 < 6 → closest 3 get images, farthest 3 are empty transparent
   Top Boss: Uploads 6 final layers
```

### 2.2 File Naming Convention (CRITICAL — per Nir)

Every image file encodes its full ancestry in the filename:

```
task_{question_id}.png                    ← Original painting uploaded by Client
task_{question_id}_01.png                 ← 1st split from Manager (Level 1, branch 01)
task_{question_id}_02.png                 ← 2nd split from Manager (Level 1, branch 02)
task_{question_id}_01_01.png              ← Teacher #1's 1st split (Level 2, branch 01→01)
task_{question_id}_01_02.png              ← Teacher #1's 2nd split (Level 2, branch 01→02)
task_{question_id}_02_01.png              ← Teacher #2's 1st split (Level 2, branch 02→01)
...
task_{question_id}_01_01_01.png           ← Worker's 1st split from Teacher #1's 1st child
```

**Rule:** Each `_NN` suffix represents one level of splitting.
The filename IS the ancestry tracker — no need to query the DB to know where it came from.
Numbers are zero-padded to 2 digits (01, 02, ... 99) per level.

The DB stores these filenames in `result_filename` / `input_image` / `split_result_1` / `split_result_2`.
The convention applies to BOTH ITG and TTG (TTG workers generate NEW images from prompts, but
when a TTG Boss combines worker results, the combined file is named `task_{parent_id}.png`).

### 2.3 Key Insight: Splitting is NOT Parallel at Each Level

Unlike TTG where 6 workers work in parallel on 6 sub-prompts, ITG's workers
work on DIFFERENT images (different branches of the split tree). Each branch
is independent — workers on different branches don't wait for each other.

But workers WITHIN a branch DO wait: a Worker can't split a layer that hasn't
been produced yet by the level above.

### 2.3 Data Flow (Complete Lifecycle)

```
Step 1: Client → Website
  POST /api/questions  { type: "ITG", file: painting.jpg }
  Website saves original to disk, records path in DB

Step 2: Boss (Manager) → Website (polling)
  GET /api/questions/pending?type=ITG
  Claims question #42

Step 3: Boss (Manager) → ComfyUI → Qwen-Image-Layered
  Downloads painting from website
  Runs split (1 image → 2 layers) using Qwen-Image-Layered
  Gets 2 RGBA layers

Step 4: Boss (Manager) → Qwen3-VL → Website
  For each of the 2 layers:
    Qwen3-VL judges: "Is this a recognizable portion of the painting?"
    If YES → upload to website, create child task
    If NO (solid color, blurry, incomprehensible) → discard

  POST /api/tasks (×N, where N = number of good layers)
  { question_id: 42, type: "ITG", depth: 1, max_depth: 2,
    parent_task_id: null, prompt: "...", input_image: "task_42_01.png" }

Step 5: Boss (Teacher) → Website → ComfyUI → Qwen3-VL → Website
  Polls: GET /api/tasks/pending?type=ITG
  Claims task with input_image "task_42_01.png"
  Downloads task_42_01.png from website
  Splits 1→2 using Qwen-Image-Layered
  Judges with Qwen3-VL → keeps good, discards garbage
  Creates child tasks at depth 2

Step 6: Worker (bottom level, depth = max_depth) → Website
  Same flow: claim → download → split 1→2 → judge → upload good layers
  But now: depth == max_depth, so NO child tasks created
  Uploads good layers as FINAL results: POST /api/tasks/{id}/result

Step 7: Boss (Teacher) → Website (polling)
  Sees ALL his children are complete
  Downloads children's result images from website
  Qwen3-VL: arranges them by Z-depth (farthest → closest)
  Uploads Z-order info: POST /api/tasks/{parent_id}/zorder
  { layers: ["task_42_01_02.png", "task_42_01_01.png"] }

Step 8: Top Boss (Manager) → Website
  Sees ALL his children (Teachers) are complete
  Downloads all final layer images + Z-order info
  Builds complete Z-ordered layer list
  If N > 6: pair-combine from farthest until 6 remain
  If N < 6: closest N get images, remaining (6-N) are empty transparent PNGs
  Uploads final 6 layers: POST /api/questions/42/complete

Step 9: Client → Website
  Polls → sees "completed"
  Downloads 6 final layers
  Displays on physical Pepper's Ghost setup

DONE.
```

---

## 3. Database Schema

Shared with TTG (see TEXT_TO_GHOST_DESIGN.md §3). Additional ITG-specific fields:

### 3.1 Questions Table — ITG Fields

```sql
-- Added to existing questions table:
input_image_path TEXT,           -- Path to uploaded original painting on website disk
input_image_url TEXT,            -- Original URL if Client provided one (NULL if file upload)
original_resolution TEXT,        -- "1920x1080" etc. (for logging)
max_depth INTEGER DEFAULT 2,     -- Default depth for ITG
depth_control_manual BOOLEAN DEFAULT 0,  -- 0 = Qwen3-VL decides, 1 = Client slider decides
```

### 3.2 Tasks Table — ITG Fields

```sql
-- Added to existing tasks table:
input_image TEXT,                -- Filename of input image for this task (from parent's split)
split_result_1 TEXT,             -- Filename of 1st output from Qwen-Image-Layered split
split_result_2 TEXT,             -- Filename of 2nd output from Qwen-Image-Layered split
quality_judgment TEXT,           -- JSON from Qwen3-VL: {"layer_1": "good", "layer_2": "garbage"}
z_order INTEGER,                 -- Assigned Z-depth position (1 = farthest, N = closest)
discarded BOOLEAN DEFAULT 0,     -- TRUE if this layer was judged as garbage
```

---

## 4. The Splitting Pipeline (Every Node)

Every node (Boss or Worker) follows the same pipeline when claiming an ITG task:

```
┌──────────────────────────────────────────────────────────┐
│                    SPLITTING PIPELINE                     │
│  (Every node: Boss & Worker — ✂️ scissors + 👁️ eyes + 🧠 brain)│
│                                                          │
│  1. Download input_image from website                    │
│     GET /api/files/task_42_01.png                        │
│                                                          │
│  2. Resize to 640×640 padded square                      │
│     Pad with transparent border for aspect ratio safety  │
│                                                          │
│  3. ✂️ SPLIT: Qwen-Image-Layered via ComfyUI             │
│     Settings: layers=2, steps=20, cfg=4.0, seed=random   │
│     Output: 2 RGBA layers                                │
│                                                          │
│  4. Save both layers locally as temp files               │
│                                                          │
│  5. 👁️ JUDGE: Qwen3-VL quality gate (each layer)         │
│     "Is this recognizable content or solid/blurry?"      │
│     Response: "good" or "garbage"                        │
│                                                          │
│  6. 👁️👁️ DESCRIBE: Qwen3-VL + 🧠🧠 BRAINSTORM: Qwen LLM   │
│     For each GOOD layer:                                 │
│     a) Qwen3-VL describes: "hookah glass with smoke"     │
│     b) Qwen LLM writes split prompt for child:           │
│        "Decompose: glass base, metal stem, smoke wisps"  │
│     c) This prompt is attached to the child task in DB   │
│                                                          │
│  7. Upload good layers to website                        │
│     POST /api/files/upload (multipart)                   │
│                                                          │
│  8a. If depth < max_depth (Boss):                        │
│      Create child tasks WITH custom prompts from step 6  │
│      POST /api/tasks/batch { tasks: [{prompt: "..."}] }  │
│                                                          │
│  8b. If depth == max_depth (Worker/bottom):              │
│      Upload good layers as final result                  │
│      POST /api/tasks/{id}/result { images: [...] }       │
│      Mark task complete                                  │
│                                                          │
│  9. Clean up local temp files                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.1 ComfyUI Integration (with Port Management)

**CRITICAL:** If Boss and Worker run on the SAME machine, they cannot share
one ComfyUI instance (40 GB UNET can only be loaded once). Each needs its
OWN ComfyUI on a different port.

```python
# In src/config.py or per-user settings:
COMFYUI_BASE_PORT = 8188

def get_comfyui_port(node_role, node_id):
    """
    Assign unique ComfyUI ports per node on the same machine.
    
    - Boss gets base port 8188
    - Additional nodes get 8189, 8190, etc.
    
    Port is stored per-user in the GUI settings (persisted to local config).
    """
    # If this node already has a running ComfyUI, reuse its port
    # Otherwise, find next free port starting from base
    for port_offset in range(10):  # Max 10 nodes per machine
        port = COMFYUI_BASE_PORT + port_offset
        if not _is_port_in_use(port):
            return port
    raise RuntimeError("No free ComfyUI ports available (8188-8198)")


def _start_comfyui_for_node(port, model_dir=None):
    """
    Start a dedicated ComfyUI instance on the given port.
    
    Each instance loads Qwen-Image-Layered models into VRAM independently.
    On RTX 5090 24GB: can run 1 instance (model is ~40GB, offloaded).
    On RTX 4070 Ti 12GB: can run 1 instance (heavy offloading).
    
    Simultaneous Boss+Worker on same GPU: NOT RECOMMENDED.
    Both would fight for VRAM. Queue them instead — the GUI serializes
    ITG tasks from the same machine.
    """
    subprocess.Popen(
        [sys.executable, COMFYUI_MAIN, "--port", str(port),
         "--output-directory", str(model_dir / "output"),
         "--input-directory", str(model_dir / "input")],
        cwd=COMFYUI_DIR,
    )
    # Wait for it to be ready
    for _ in range(30):
        time.sleep(2)
        if _is_comfyui_running(port):
            return port
    raise RuntimeError(f"ComfyUI failed to start on port {port}")


# In the GUI: each user (Boss/Worker tab) gets a ComfyUI port setting
# If Boss and Worker are on the same machine, they SHARE the same ComfyUI
# and the GUI serializes their tasks (don't run splits in parallel).
# If on different machines, they have independent instances — true parallelism.
```

### 4.2 Split Function (Using Managed ComfyUI)

```python
def split_image_into_2_layers(input_image_path, output_dir, comfyui_port, seed=None):
    """
    Split one RGBA image into 2 layers using Qwen-Image-Layered via ComfyUI.

    Returns: (layer_1_path, layer_2_path) — both RGBA PNG files.
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    # Resize to 640x640 with padding (preserves aspect ratio, no extreme shapes)
    img = _prepare_for_qwen(input_image_path)
    prep_path = os.path.join(output_dir, f"split_input_{uuid4().hex[:6]}.png")
    img.save(prep_path, "PNG")

    # Upload to ComfyUI
    image_name = _comfy_upload_image(prep_path, port=comfyui_port)

    # Build and submit workflow
    workflow = _build_split_workflow(
        image_name=image_name, layers=2, steps=20,
        cfg=4.0, seed=seed, prompt="",
    )
    prompt_id = _comfy_submit(workflow, port=comfyui_port)
    output_files = _comfy_wait_and_download(prompt_id, output_dir, port=comfyui_port)

    # Filter: expect 3 files (2 layers + 1 composite), keep the 2 layer files
    layer_files = [f for f in output_files if not f.endswith('_00001_.png')]
    if len(layer_files) != 2:
        raise RuntimeError(f"Expected 2 layers, got {len(layer_files)}")

    return layer_files[0], layer_files[1]


def _prepare_for_qwen(image_path, target_size=640):
    """
    Resize image to fit within target_size × target_size with PADDING.
    
    thumbnail() preserves aspect ratio but can produce extreme rectangles
    (e.g., 640×50 for a panoramic painting). Qwen-Image-Layered's MMDiT
    expects near-square inputs. We pad to square to avoid artifacts.
    """
    img = Image.open(image_path).convert("RGBA")
    img.thumbnail((target_size, target_size), Image.LANCZOS)
    
    # Create square canvas with transparent padding
    square = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    offset_x = (target_size - img.width) // 2
    offset_y = (target_size - img.height) // 2
    square.paste(img, (offset_x, offset_y))
    
    return square
```

### 4.3 Qwen3-VL Quality Gate

```python
def judge_layer_quality(image_path, original_painting_desc=""):
    """
    Ask Qwen3-VL (via Ollama or LM-Studio) whether a layer is worth keeping.

    Returns: {"quality": "good" | "garbage", "description": "...", "confidence": 0.0-1.0}
    """
    # Encode image as base64 for Ollama vision API
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    prompt = """You are a quality control judge for an image decomposition pipeline.

    Look at this image. It is supposed to be ONE depth layer extracted from a larger artwork.
    
    Answer these questions:
    1. Is this image mostly a solid single color (like all black, all white, all gray)?
    2. Is this image blurry beyond recognition?
    3. Does this image contain recognizable content from the original artwork?
    4. Is this image worth keeping for a multi-layer Pepper's Ghost display?

    Respond with ONLY this JSON:
    {"quality": "good" or "garbage", "description": "brief description of contents", "confidence": 0.0-1.0}
    """

    response = ollama.generate(
        model="qwen3-vl:4b",  # Smallest VL model — enough for quality check
        prompt=prompt,
        images=[img_b64],
    )

    return json.loads(response)


def handle_dual_garbage(parent_task, split_result_1, split_result_2):
    """
    CRITICAL EDGE CASE: Both split layers from Qwen-Image-Layered are garbage.
    
    If we discard both, the parent task stays in "claimed" state forever
    — no children, no result. The whole branch dies silently.
    
    Strategy:
    1. Re-upload the ORIGINAL input image as a single child
    2. Different seed + CFG for next attempt (maximize chance of a good split)
    3. Max 3 retries per branch — after that, mark as failed (image is unsplittable)
    """
    from src.logger import logger
    
    retry = parent_task.get('retry_count', 0) + 1
    
    if retry >= 3:
        logger.error(f"Task {parent_task['id']}: 3 dual-garbage splits. "
                     f"Branch dead — image is fundamentally unsplittable.")
        parent_task['status'] = 'failed'
        parent_task['error'] = 'Unsplitabble image after 3 retries'
        PATCH /api/tasks/{parent_task['id']}  { status: 'failed' }
        return
    
    logger.warning(f"Task {parent_task['id']}: BOTH outputs garbage (retry {retry}/3). "
                   f"Creating fallback child with randomized seed.")
    
    # Re-upload original as child input
    original = download_image(parent_task['input_image'])
    child_filename = parent_task['input_image'].replace('.png', f'_r{retry}.png')
    upload_image(original, child_filename)
    
    # Create ONE child (not two — don't duplicate the problem)
    create_child_task(
        parent_task_id=parent_task['id'],
        depth=parent_task['depth'] + 1,
        max_depth=parent_task['max_depth'],
        input_image=child_filename,
        prompt="",
        retry_count=retry,
    )
```

### 4.4 Prompts for Qwen-Image-Layered (The Unresolved Problem)

We know from MEMORY.md (extensive testing May 21) that:
- **Empty prompt** (`""`) often works BETTER than wrong prompts
- **Multiline prompts** (one line per target layer) may improve per-layer targeting
- **The model decides autonomously** based on depth and occlusion — we can SUGGEST but not CONTROL

Strategy for ITG:
- **Level 0 (Manager):** Broad split: "distant background elements, close foreground elements"
- **Level 1+ (Teachers/Workers):** More specific: whatever the parent Boss provides as `prompt`
- **Prompt format:** Comma-separated list matching layer count, foreground first

```python
DEFAULT_SPLIT_PROMPTS = {
    0: "distant background and sky elements, midground objects and scenery, close foreground details and characters",
    1: "",  # Empty — let model decide autonomously for deeper levels
    2: "",  # Empty
}
```

---

## 5. Z-Ordering (On the Way Back Up)

### 5.1 The Complete Flow — Step by Step

```
TOP BOSS (Manager) does NOT download ALL final layers directly.
Instead, the Z-order flows UP through the hierarchy:

┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Bottom-level Workers upload their final good layers │
│   Worker W1: Uploads task_42_01_01.png (from split 1)       │
│   Worker W1: Uploads task_42_01_02.png (from split 2)       │
│   Worker W2: Uploads task_42_02_01.png                       │
│   (Each uploads to: POST /api/tasks/{id}/result)            │
├─────────────────────────────────────────────────────────────┤
│ STEP 2: Teacher #1 polls — sees both children complete      │
│   Downloads: task_42_01_01.png + task_42_01_02.png           │
│   Qwen3-VL (pairwise): which of these 2 is farther?         │
│   Uploads Z-order metadata:                                  │
│     PUT /api/tasks/{teacher1_id}/zorder                     │
│     {                                                       │
│       "layers": [                                           │
│         "task_42_01_02.png",  ← farthest (background)       │
│         "task_42_01_01.png"   ← closest (foreground)        │
│       ]                                                     │
│     }                                                       │
├─────────────────────────────────────────────────────────────┤
│ STEP 3: Teacher #2 does the same for HIS children            │
│   Downloads: task_42_02_01.png (only 1 — other was garbage) │
│   Single layer: no Z-order needed (auto = only layer)       │
│   Uploads Z-order metadata:                                  │
│     PUT /api/tasks/{teacher2_id}/zorder                     │
│     {                                                       │
│       "layers": ["task_42_02_01.png"]                       │
│     }                                                       │
├─────────────────────────────────────────────────────────────┤
│ STEP 4: Top Boss polls — sees ALL teachers complete          │
│   Top Boss downloads:                                        │
│     — Teacher #1's zorder: ["task_42_01_02.png",            │
│                              "task_42_01_01.png"]            │
│     — Teacher #2's zorder: ["task_42_02_01.png"]            │
│                                                              │
│   Top Boss downloads the actual images:                      │
│     GET /api/files/task_42_01_02.png                         │
│     GET /api/files/task_42_01_01.png                         │
│     GET /api/files/task_42_02_01.png                         │
│                                                              │
│   Top Boss runs Qwen3-VL pairwise Z-order on them:           │
│     "task_42_01_02.png is farthest"                          │
│     "task_42_02_01.png is middle"                            │
│     "task_42_01_01.png is closest"                           │
│                                                              │
│   Result: 3 layers. N=3 < 6 → place real layers at closest     │
│   positions (L1-L3), remaining (L4-L6) empty transparent.       │
│   Layer convention: L1=closest(20cm) → L6=farthest              │
│                                                              │
│   Top Boss uploads: POST /api/questions/42/complete          │
│     layer_1.png = task_42_01_01.png  (CLOSEST real layer)    │
│     layer_2.png = task_42_02_01.png  (middle real layer)     │
│     layer_3.png = task_42_01_02.png  (FARTHEST real layer)   │
│     layer_4.png = empty transparent                          │
│     layer_5.png = empty transparent                          │
│     layer_6.png = empty transparent                          │
│                                                              │
│ DONE. Client downloads 6 layers.                             │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** Top Boss does NOT download every single layer from every worker.
He downloads the Z-order METADATA from his direct children (the Teachers).
That metadata tells him which filenames to download and in what order.
Then he does ONE final Z-ordering pass on the collected layers, followed by combining.

### 5.2 What Each Boss Level Does

| Boss Level | Downloads from children | Uploads |
|-----------|------------------------|---------|
| **Teacher (mid-level)** | Children's result images | Z-order metadata for HIS children's layers |
| **Manager (top level)** | Z-order metadata from all teachers + the actual images | Final 6 layers |

Mid-level bosses NEVER combine. They only arrange. The top boss is the only combiner.

### 5.3 Z-Order Implementation: Pairwise Comparison (Ollama-Compatible)

**CRITICAL:** Ollama's vision API supports ONE image per message, not multiple.
We cannot send N images and ask "arrange them." Instead, use pairwise comparison:

```python
def determine_z_order(layer_paths):
    """
    Arrange N images by depth using pairwise Qwen3-VL comparisons.
    
    Ollama-compatible: each call sends exactly 2 images + prompt.
    
    Returns: list of paths sorted farthest→closest.
    """
    if len(layer_paths) <= 1:
        return list(layer_paths)
    
    # Sort using pairwise comparisons (like a tournament)
    # For each pair, ask: "Which of these two is farther from the viewer?"
    
    # Start with first image as "current farthest"
    sorted_layers = [layer_paths[0]]
    
    for new_path in layer_paths[1:]:
        # Compare new_path against each already-sorted layer to find its position
        inserted = False
        for i, existing in enumerate(sorted_layers):
            result = _pairwise_compare(new_path, existing)  # returns: "A_farther" or "B_farther"
            if result == "A_farther":  # new is farther than existing
                sorted_layers.insert(i, new_path)
                inserted = True
                break
        if not inserted:
            sorted_layers.append(new_path)  # new is closest of all
    
    return sorted_layers


def _pairwise_compare(image_a_path, image_b_path):
    """
    Ask Qwen3-VL: "Which of these two layers is farther from the viewer?"
    
    Returns: "A_farther" or "B_farther"
    """
    with open(image_a_path, "rb") as f:
        img_a_b64 = base64.b64encode(f.read()).decode()
    with open(image_b_path, "rb") as f:
        img_b_b64 = base64.b64encode(f.read()).decode()
    
    prompt = """You see two transparent image layers extracted from the same artwork.
    Which one is FARTHER from the viewer (background)?
    
    Consider: sky/horizon = farthest. Characters/foreground objects = closest.
    Larger objects, more detail, warmer colors = closer to the viewer.
    
    Respond ONLY with: "A" or "B"
    (A = the first image, B = the second image)"""
    
    response = ollama.chat(
        model="qwen3-vl:4b",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [img_a_b64, img_b_b64]
        }]
    )
    
    answer = response["message"]["content"].strip().upper()
    if "A" in answer:
        return "A_farther"
    else:
        return "B_farther"
```

**Performance:** N layers → ~N²/2 pairwise comparisons. For typical N=2-6 layers, this is 1-15 comparisons.
Each comparison call to Ollama: ~0.5-1 second. Total: <15 seconds for worst case.

**Which to use:** Qwen3-VL pairwise comparison ONLY. No programmatic fallback — it cannot work (giant cloud = high coverage ≠ closer than tiny character). If Qwen3-VL is unavailable, the task waits. If Qwen3-VL is wrong, the output is wrong — cost of full automation. Only a human can override.

**Helper: Propagate Client's original prompt.** If the Client described depth in their submission (e.g., "foreground: hookah glass, middle: smoke, background: mystical mist"), each entity receives this context alongside the image. Qwen3-VL uses it as a hint when comparing layers pairwise.

---

## 6. Combining (Top Boss Only)

### 6.1 When to Combine

Only the **top-level Boss** (depth 0, the Manager) combines. All intermediate Bosses
ONLY arrange Z-order — they do NOT combine.

### 6.2 The Pair-From-Farthest Algorithm

```python
def reduce_to_6_layers(z_ordered_paths):
    """
    Given N RGBA layers in Z-order: index 0 = CLOSEST (Layer 1, 20cm from viewer),
    index N-1 = FARTHEST (Layer N, deepest background).

    Always combine from the FARTHEST end (end of list) — minimal parallax there.
    Never combine the closest 4 layers (start of list) — strong parallax.

    Returns: list of exactly 6 paths, index 0 = closest, index 5 = farthest.
    """
    N = len(z_ordered_paths)

    if N == 6:
        return z_ordered_paths  # Already perfect

    if N < 6:
        # Real layers at closest positions (L1-LN), empty transparent at farthest (L(N+1)-L6)
        result = list(z_ordered_paths)  # Real layers first (closest)
        for _ in range(6 - N):
            result.append(create_empty_transparent_png())  # Empty far layers at end
        return result

    # N > 6: Combine pairs from FARTHEST (end of list) until 6 remain
    layers = list(z_ordered_paths)  # index 0 = closest, index N-1 = farthest

    while len(layers) > 6:
        # Combine the TWO FARTHEST layers (at the end of the list)
        back = Image.open(layers[-2]).convert("RGBA")
        front = Image.open(layers[-1]).convert("RGBA")
        combined = Image.alpha_composite(back, front)
        
        combined_path = f"combined_{uuid4().hex[:6]}.png"
        combined.save(combined_path, "PNG")

        # Remove the 2 farthest, insert combined at end (farthest position)
        layers = layers[:-2] + [combined_path]

    return layers  # Exactly 6: index 0 = closest (20cm), index 5 = farthest

### 6.3 Why Not Combine Closest Layers

Per Nir's physical testing: close layers produce strong parallax when the viewer moves
their head. Combining them fuses the 3D depth information. Far layers (sky, mountains,
distant forest) have MINIMAL parallax — combining them is invisible to the viewer.

---

## 7. GUI Design (ITG Tab)

### 7.1 ITG Tab — Client View

```
┌──────────────────────────────────────────────────┐
│  Upload Painting:                                 │
│  ┌─────────────────────────────────────────────┐  │
│  │  [ Choose File ]  or  [ Paste URL ]         │  │
│  │  opium_dream.jpg (1920×1080, 2.3 MB)        │  │
│  │  [Preview of uploaded image]                 │  │
│  └─────────────────────────────────────────────┘  │
│                                                   │
│  Depth:                                           │
│  ☐ Let AI decide (Qwen3-VL)   ← default (off)    │
│  ☑ Manual depth: [ 2  ▬▬▬▬▼ ]                  │
│  (2 = split to 2, pass down. Higher = more splits)│
│                                                   │
│  [ Submit for Decomposition ]                     │
│                                                   │
│  ── Status ───────────────────────────────────── │
│  Question #44 | Status: decomposing... ⏳         │
│  Depth tree: 1→2→4→5 good layers so far          │
│  [Download Layer 1] ... [Download Layer 6]        │
└──────────────────────────────────────────────────┘
```

### 7.2 ITG Tab — Boss View

```
┌──────────────────────────────────────────────────┐
│  Boss ID: [ manager_01             ]             │
│  ComfyUI:  http://127.0.0.1:8188  [Test]        │
│  Qwen3-VL: [ qwen3-vl:4b ▼ ]     [Test]         │
│                                                   │
│  ── Pending Questions ────────────────────────── │
│  ┌────────────────────────────────────────────┐   │
│  │ #44 | Opium Dream (ITG) | pending  | [Take]│   │
│  │ #45 | Starry Night (ITG) | pending | [Take]│   │
│  └────────────────────────────────────────────┘   │
│                                                   │
│  ── Active Question #44 ──────────────────────── │
│  Depth: 1 of 2 | Input: task_44.png              │
│                                                   │
│  My Split Results:                                │
│  ┌────────────────────────────────────────────┐   │
│  │ Layer A [Preview]  ✓ good → created child  │   │
│  │ Layer B [Preview]  ✗ garbage → discarded   │   │
│  └────────────────────────────────────────────┘   │
│                                                   │
│  My Children (1 task created):                    │
│  ┌────────────────────────────────────────────┐   │
│  │ #201 | depth:2 | input: task_44_01 | working│   │
│  └────────────────────────────────────────────┘   │
│                                                   │
│  [Split & Judge]  [Arrange Z-Order]  [Upload]     │
└──────────────────────────────────────────────────┘
```

### 7.3 ITG Tab — Worker View

```
┌──────────────────────────────────────────────────┐
│  Worker ID: [ worker_03              ]            │
│  ComfyUI:  http://127.0.0.1:8188  [Test]        │
│  Qwen3-VL: [ qwen3-vl:4b ▼ ]     [Test]         │
│                                                   │
│  ── Available Tasks ──────────────────────────── │
│  ┌────────────────────────────────────────────┐   │
│  │ #201 | ITG | depth:2 | input: task_44_01   │   │
│  │        Split into 2 layers        [Claim]  │   │
│  └────────────────────────────────────────────┘   │
│                                                   │
│  ── Active Task #201 ─────────────────────────── │
│  Input Image: [Preview of task_44_01.png]         │
│  [ Split (1→2) ]                                  │
│                                                   │
│  Split Results:                                   │
│  Layer 1: [Preview] ── Qwen3-VL says: ✓ good     │
│    [Upload as Final]                              │
│  Layer 2: [Preview] ── Qwen3-VL says: ✗ garbage  │
│    [Discard]                                      │
│                                                   │
│  [Upload All Good Layers & Complete]              │
└──────────────────────────────────────────────────┘
```

---

## 8. Flask API — ITG-Specific Endpoints

### 8.1 New Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/questions` | Client submits: multipart with `file` + `type: "ITG"` + `max_depth` |
| GET | `/api/files/<filename>` | Download any image file (shared with TTG) |
| POST | `/api/files/upload` | Any node uploads an image: multipart file + `task_id` context |
| PUT | `/api/tasks/<id>/zorder` | Boss uploads Z-order arrangement for children's results |
| GET | `/api/questions/<id>/tree` | Returns full task tree for visualization |
| GET | `/api/questions/<id>/stats` | Returns stats: total tasks, completed, discarded, good layers |
| DELETE | `/api/questions/<id>/cleanup` | Delete all intermediate files, keep only originals + finals |

### 8.2 File Upload Endpoint Detail

```
POST /api/files/upload
Content-Type: multipart/form-data

Fields:
  file: (binary PNG data)
  task_id: 201
  layer_index: 1 or 2   (which split output this is)
  is_final: true/false   (is this a bottom-level result or intermediate?)

Response:
  {
    "filename": "task_42_01_01.png",
    "path": "/output/itg/temp/task_42_01_01.png",
    "size_bytes": 12345
  }
```

---

## 9. Prompt Strategy (What We Know vs What We Don't)

### 9.1 What We Know (from MEMORY.md testing)

| What | Evidence |
|------|----------|
| Empty prompt works | Starry Night decomposed with `""` prompt — 7 layers produced |
| Comma-separated is better | Google Q5: "exactly as many items as layer count" |
| Multiline may fix one-layer problem | Google Q9: single text = model assumes 1-layer target |
| Don't describe art style | Claude/Gemini: describing style causes regeneration, not preservation |
| Low CFG preserves original | CFG 2.0-4.0 preserves brushstrokes; higher CFG hallucinates |
| 640px is the sweet spot | Model trained at 640; 1024+ causes artifacting |

### 9.2 Recommended Prompt Strategy Per Level

| Depth | Prompt | Rationale |
|-------|--------|-----------|
| 0 (Manager) | `"distant background sky and horizon, midground scene elements and structures, close foreground details and characters"` | Broad enough for first split |
| 1 (Teacher) | Empty `""` | Model knows the image now; autonomous is better |
| 2+ (Worker) | Empty `""` | Let model decide — too specific at this depth causes hallucination |

### 9.3 The Prompt "We Still Need to Figure Out"

We don't yet have a reliable prompt that makes Qwen-Image-Layered produce non-garbage layers
for fine art paintings. The model was trained on Photoshop PSDs (photos + graphic design),
not impressionist brushwork.

**Fallback plan:** If quality is consistently bad, try:
1. Run without prompt (autonomous — worked for Starry Night)
2. Use recursive decomposition (split 2, feed good back in, repeat)
3. Accept that some paintings won't work (physical medium limitation)

---

## 10. Implementation Plan

### Phase 1: Shared Infrastructure (with TTG)
1. Database schema changes (type, depth, parent_task_id, ITG fields)
2. New API endpoints (files, zorder, tree, stats, cleanup)
3. File storage system (temp vs final directory structure)
4. Ensure all 17 existing TTG API tests still pass

### Phase 2: ComfyUI Integration
1. Refactor `run_comfy_decomp.py` into reusable `src/itg_splitter.py`
2. Function: `split_image_into_n_layers(image_path, n=2, ...)` → list of paths
3. Wrap ComfyUI upload/submit/wait/download in a clean module
4. Test with one painting → verify 2 RGBA layers produced

### Phase 3: Qwen3-VL Integration
1. Module: `src/itg_judge.py`
2. Function: `judge_layer_quality(image_path)` → {quality, description, confidence}
3. Function: `determine_z_order(layer_paths)` → [sorted indices]
4. Test with real good and bad layers

### Phase 4: ITG Node Logic
1. `src/itg_node.py` — the splitting pipeline for every node
2. Boss logic: split → judge → create children or upload final
3. Worker logic: split → judge → upload final (no children)
4. Z-order on way up: when all children complete, arrange and upload

### Phase 5: ITG GUI Tab
1. Client view: file upload, depth slider, status polling
2. Boss view: pending questions, split preview, children status
3. Worker view: pending tasks, split preview, quality judgment display

### Phase 6: Combining
1. `src/itg_combine.py` — pair-from-farthest algorithm
2. Top boss: download all final layers, run combining, upload 6
3. Handle N < 6 (empty transparent layers)
4. Handle N > 6 (pair combining)

### Phase 7: Testing
1. Local test: one computer does Manager + 2 Workers (simulated)
2. LAN test: Laptop (website + Manager + Worker) + Desktop (Worker)
3. Internet test via Cloudflared

---

## 11. Edge Cases & Failure Handling

| Scenario | Handling |
|----------|----------|
| **All layers garbage** | Top boss creates 6 empty transparent PNGs, marks question complete with warning |
| **Dual-garbage split (both layers bad)** | Handle with `handle_dual_garbage()`: retry with original image + new seed, max 3 retries before marking branch dead (see §4.3) |
| **ComfyUI crash mid-split** | Caught by try/except → task reset to pending → another worker picks up |
| **Qwen3-VL unavailable** | Task waits. No programmatic fallback (unreliable — giant cloud vs tiny character). Only human can override Z-order. |
| **N = 0 good layers** | Mark question as `failed`, notify Client |
| **N = 1 good layer** | Put it at L1 (closest, 20cm), L2-L6 empty transparent |
| **N < 6 layers** | Closest layers (L1-LN) get real images, remaining farthest (L(N+1)-L6) are empty transparent PNGs (see §6.2). L1=20cm closest, L6=farthest. |
| **Pre-built ComfyUI models missing** | Node checks on startup, warns user to download models (links to setup guide) |
| **Disk full on website** | `GET /api/health` returns disk space warning; Boss pauses creating new tasks |
| **Worker disconnects mid-job** | Task auto-resets to pending after timeout (e.g., 10 minutes with no progress) |
| **Boss+Worker same machine ComfyUI conflict** | Single ComfyUI instance shared; GUI serializes tasks (see §4.1); if port conflict, auto-find next free port |
| **Extreme aspect ratio input** | Pad to 640×640 square with transparent border before sending to Qwen-Image-Layered (see §4.2 `_prepare_for_qwen`) |

---

## 12. Open Questions

1. **Qwen3-VL model size?** Which size works? 4B (light, fast, might miss nuance) vs 8B (better, heavier) vs 32B (overkill)?
2. **Is Qwen3-VL in Ollama?** Need to verify availability for vision tasks. If not, LM-Studio fallback.
3. **Prompt for Qwen-Image-Layered — unsolved.** We still don't have a reliably working prompt for fine art. Need more testing.
4. **SageAttention + Triton for diffusers?** Might allow Python-native splitting (no ComfyUI). Worth investigating again after building.
5. **How many workers per Boss?** Should a teacher create exactly 2 child tasks (since split is 1→2)? Or should a teacher run multiple splits and create more?
6. **Timeouts?** How long before a claimed-but-not-completed task resets to pending?

---

*End of IMAGE_TO_GHOST_DESIGN.md*
