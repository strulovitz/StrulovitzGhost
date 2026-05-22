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

### 2.2 Key Insight: Splitting is NOT Parallel at Each Level

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
│                                                          │
│  1. Download input_image from website                    │
│     GET /api/files/task_42_01.png                        │
│                                                          │
│  2. Resize to 640px (longest side)                       │
│     Maintains aspect ratio. Required by Qwen-Image-Layered│
│                                                          │
│  3. Run Qwen-Image-Layered via ComfyUI                   │
│     Settings: layers=2, steps=20, cfg=4.0, seed=random   │
│     Input: resized RGBA image                            │
│     Output: 2 RGBA layers (split_result_1, split_result_2)│
│                                                          │
│  4. Save both layers locally as temp files               │
│                                                          │
│  5. Qwen3-VL Quality Gate (for each of the 2 layers)     │
│     Send image to Qwen3-VL: "Is this image recognizable  │
│     as part of the original artwork, or is it a solid    │
│     color / blurry / incomprehensible?"                  │
│     Response: "good" or "garbage"                        │
│                                                          │
│  6. Upload good layers to website                        │
│     POST /api/files/upload (multipart: task_42_01_01.png)│
│                                                          │
│  7a. If depth < max_depth (Boss):                        │
│      Create 2 child tasks (or 1 if one layer garbage)    │
│      POST /api/tasks/batch { tasks: [...] }              │
│                                                          │
│  7b. If depth == max_depth (Worker/bottom):              │
│      Upload good layers as final result                  │
│      POST /api/tasks/{id}/result { images: [...] }       │
│      Mark task complete                                  │
│                                                          │
│  8. Clean up local temp files                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.1 ComfyUI Integration

```python
def split_image_into_2_layers(input_image_path, output_dir, seed=None):
    """
    Split one RGBA image into 2 layers using Qwen-Image-Layered via ComfyUI.

    Returns: (layer_1_path, layer_2_path) — both RGBA PNG files.
    Layer 1 = foreground, Layer 2 = background (per Qwen-Image-Layered convention).
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    # Resize input to 640px
    img = Image.open(input_image_path).convert("RGBA")
    img.thumbnail((640, 640), Image.LANCZOS)
    prep_path = os.path.join(output_dir, f"split_input_{uuid4().hex[:6]}.png")
    img.save(prep_path, "PNG")

    # Upload to ComfyUI
    image_name = _comfy_upload_image(prep_path)

    # Build workflow (reuse existing run_comfy_decomp.py pattern)
    workflow = _build_split_workflow(
        image_name=image_name,
        layers=2,
        steps=20,
        cfg=4.0,
        seed=seed,
        prompt="",  # Empty prompt = autonomous decomposition
    )

    # Submit and wait
    prompt_id = _comfy_submit(workflow)
    output_files = _comfy_wait_and_download(prompt_id, output_dir)

    # output_files should have 3 files (2 layers + 1 composite)
    # Filter out composite, keep the 2 layer files
    layer_files = [f for f in output_files if not f.endswith('_00001_.png')]
    if len(layer_files) != 2:
        raise RuntimeError(f"Expected 2 layers, got {len(layer_files)}")

    return layer_files[0], layer_files[1]
```

### 4.2 Qwen3-VL Quality Gate

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
```

### 4.3 Prompts for Qwen-Image-Layered (The Unresolved Problem)

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

### 5.1 What Happens

When a Boss's children complete:
1. Download all children's result images
2. Send ALL images to Qwen3-VL in one batch
3. Qwen3-VL arranges them from farthest to closest
4. Boss uploads Z-order metadata

### 5.2 Qwen3-VL Z-Order Prompt

```python
def determine_z_order(layer_paths, original_painting_path=None):
    """
    Ask Qwen3-VL to arrange N images by depth (farthest from viewer → closest to viewer).
    Returns list of paths in Z-order.
    """
    images_b64 = []
    for path in layer_paths:
        with open(path, "rb") as f:
            images_b64.append(base64.b64encode(f.read()).decode())

    prompt = f"""You are looking at {len(layer_paths)} transparent image layers
    extracted from the same artwork. Your job: arrange them by depth.

    Layer 1 = FARTHEST from the viewer (sky, distant background, horizon)
    Layer {len(layer_paths)} = CLOSEST to the viewer (foreground objects, characters)

    List layer numbers from 1 (farthest) to {len(layer_paths)} (closest).
    
    Respond with ONLY this JSON:
    {{"z_order": [1, 3, 2, ...]}}  (indices: 1-based, in farthest→closest order)
    """

    # This requires a model that can take multiple images. 
    # Ollama supports this in the chat API with multiple image parts.
    # Alternative: judge pairwise and build a sort order.
    
    response = ollama.chat(
        model="qwen3-vl:8b",
        messages=[{"role": "user", "content": prompt, "images": images_b64}],
    )
    return json.loads(response)["z_order"]
```

### 5.3 Alternative: Programmatic Z-Order

If Qwen3-VL multi-image is unreliable:

```python
def determine_z_order_programmatic(layer_paths):
    """
    Heuristic: larger objects = closer. More alpha coverage = closer.
    Fall back to manual ordering if AI fails.
    """
    scores = []
    for path in layer_paths:
        img = Image.open(path).convert("RGBA")
        arr = np.array(img)
        alpha = arr[:, :, 3]
        
        # Score: percentage of non-transparent pixels
        coverage = np.sum(alpha > 0) / (img.width * img.height)
        
        # Score: average "connected component" size (bigger = closer)
        # Simplified: just use coverage as proxy
        scores.append(coverage)
    
    # Sort by coverage ascending (less coverage = farther, typically sky/background)
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i])
    return [i + 1 for i in sorted_indices]  # 1-based indices
```

---

## 6. Combining (Top Boss Only)

### 6.1 When to Combine

Only the **top-level Boss** (depth 0, the Manager) combines. All intermediate Bosses
ONLY arrange Z-order — they do NOT combine.

### 6.2 The Pair-From-Farthest Algorithm

```python
def reduce_to_6_layers(z_ordered_paths):
    """
    Given N RGBA layers in Z-order (index 0 = farthest, index N-1 = closest),
    reduce to exactly 6 layers.

    Always combine from the FARTHEST end — minimal parallax there.
    Never combine the closest 4 layers (strong parallax).

    Returns: list of exactly 6 paths (new combined files).
    """
    N = len(z_ordered_paths)

    if N == 6:
        return z_ordered_paths  # Already perfect

    if N < 6:
        # Not enough layers. Closest get actual images, farthest are empty.
        result = []
        empty_count = 6 - N
        for i in range(empty_count):
            result.append(create_empty_transparent_png())  # Transparent 640px PNG
        for path in z_ordered_paths:
            result.append(path)
        return result

    # N > 6: Combine pairs from farthest until 6 remain
    layers = list(z_ordered_paths)  # index 0 = farthest

    while len(layers) > 6:
        # Combine the TWO FARTHEST layers
        farthest_2 = layers[:2]
        combined = Image.open(farthest_2[0]).convert("RGBA")
        overlay = Image.open(farthest_2[1]).convert("RGBA")
        combined = Image.alpha_composite(combined, overlay)
        
        combined_path = f"combined_{uuid4().hex[:6]}.png"
        combined.save(combined_path, "PNG")

        # Remove the 2 farthest, insert combined at front (farthest position)
        layers = [combined_path] + layers[2:]

    return layers  # Exactly 6
```

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
| **ComfyUI crash mid-split** | Caught by try/except → task reset to pending → another worker picks up |
| **Qwen3-VL unavailable** | Fall back to heuristic: coverage-based quality + programmatic Z-order |
| **N = 0 good layers** | Mark question as `failed`, notify Client |
| **N = 1 good layer** | Put it at Layer 1 (closest), 5 empty transparent layers |
| **Pre-built ComfyUI models missing** | Node checks on startup, warns user to download models (links to setup guide) |
| **Disk full on website** | `GET /api/health` returns disk space warning; Boss pauses creating new tasks |
| **Worker disconnects mid-job** | Task auto-resets to pending after timeout (e.g., 10 minutes with no progress) |

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
