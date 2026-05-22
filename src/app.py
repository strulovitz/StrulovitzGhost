import os, sys, shutil, glob, json as json_module
from logger import setup_logging
setup_logging()

from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

from config import DATABASE_URL, SECRET_KEY, OUTPUT_DIR, LLM_PROVIDER, LLM_MODEL, LLM_SPLIT_ENABLED
from models import db, Question, Task, QuestionStatus, TaskStatus, JobType

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

ALLOWED_EXTENSIONS = {"png"}
OUTPUT_ROOT = os.path.join(os.path.dirname(__file__), "output")
TTG_TEMP = os.path.join(OUTPUT_ROOT, "ttg", "temp")
TTG_FINAL = os.path.join(OUTPUT_ROOT, "ttg", "final")
ITG_TEMP = os.path.join(OUTPUT_ROOT, "itg", "temp")
ITG_FINAL = os.path.join(OUTPUT_ROOT, "itg", "final")
ORIGINALS = os.path.join(OUTPUT_ROOT, "originals")

for d in [TTG_TEMP, TTG_FINAL, ITG_TEMP, ITG_FINAL, ORIGINALS]:
    os.makedirs(d, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def task_to_dict(t):
    return {
        "id": t.id,
        "question_id": t.question_id,
        "type": t.type.value if t.type else "TTG",
        "parent_task_id": t.parent_task_id,
        "depth": t.depth,
        "max_depth": t.max_depth,
        "layer_number": t.layer_number,
        "prompt": t.prompt,
        "negative_prompt": t.negative_prompt,
        "status": t.status.value,
        "worker_id": t.worker_id,
        "result_filename": t.result_filename,
        "input_image": t.input_image,
        "split_result_1": t.split_result_1,
        "split_result_2": t.split_result_2,
        "quality_judgment": json_module.loads(t.quality_judgment) if t.quality_judgment else None,
        "z_order": t.z_order,
        "discarded": t.discarded,
        "retry_count": t.retry_count,
        "created_at": t.created_at.isoformat(),
        "claimed_at": t.claimed_at.isoformat() if t.claimed_at else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
    }


def question_to_dict(q, include_tasks=True):
    base = {
        "id": q.id,
        "type": q.type.value if q.type else "TTG",
        "description": q.description,
        "style": q.style,
        "status": q.status.value,
        "global_negative_prompt": q.global_negative_prompt,
        "input_image_path": q.input_image_path,
        "input_image_url": q.input_image_url,
        "original_resolution": q.original_resolution,
        "max_depth": q.max_depth,
        "depth_control_manual": q.depth_control_manual,
        "created_at": q.created_at.isoformat(),
        "completed_at": q.completed_at.isoformat() if q.completed_at else None,
    }
    if include_tasks:
        base["tasks"] = [task_to_dict(t) for t in q.tasks]
    return base


# ─── Existing Endpoints (updated) ────────────────────────────────────

@app.route("/")
def index():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template("index.html", questions=questions)


@app.route("/api/question", methods=["POST"])
def submit_question():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "request body is required"}), 400

    job_type = data.get("type", "TTG").upper()
    if job_type not in ("TTG", "ITG"):
        return jsonify({"error": "type must be TTG or ITG"}), 400

    if job_type == "TTG" and "description" not in data:
        return jsonify({"error": "description is required for TTG"}), 400

    question = Question(
        type=JobType(job_type),
        description=data.get("description"),
        style=data.get("style"),
        global_negative_prompt=data.get("global_negative_prompt"),
        max_depth=data.get("max_depth", 0),
        depth_control_manual=data.get("depth_control_manual", False),
    )
    db.session.add(question)
    db.session.commit()
    return jsonify(question_to_dict(question)), 201


@app.route("/api/question/upload", methods=["POST"])
def upload_itg_question():
    if "file" not in request.files:
        return jsonify({"error": "image file is required for ITG"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "valid PNG file is required"}), 400

    url = request.form.get("url", None)
    max_depth = int(request.form.get("max_depth", 2))
    depth_manual = request.form.get("depth_control_manual", "0") == "1"

    filename = secure_filename(file.filename)
    filepath = os.path.join(ORIGINALS, filename)
    file.save(filepath)

    from PIL import Image
    img = Image.open(filepath)
    resolution = f"{img.width}x{img.height}"

    question = Question(
        type=JobType.ITG,
        description=request.form.get("description", "Painting decomposition"),
        input_image_path=filepath,
        input_image_url=url,
        original_resolution=resolution,
        max_depth=max_depth,
        depth_control_manual=depth_manual,
    )
    db.session.add(question)
    db.session.commit()
    return jsonify(question_to_dict(question)), 201


@app.route("/api/questions", methods=["GET"])
def list_questions():
    status_filter = request.args.get("status")
    type_filter = request.args.get("type")
    query = Question.query
    if status_filter:
        query = query.filter(Question.status == status_filter)
    if type_filter:
        query = query.filter(Question.type == type_filter.upper())
    questions = query.order_by(Question.created_at.desc()).all()
    return jsonify([question_to_dict(q) for q in questions])


@app.route("/api/question/<int:question_id>", methods=["GET"])
def get_question(question_id):
    question = Question.query.get_or_404(question_id)
    return jsonify(question_to_dict(question))


@app.route("/api/question/<int:question_id>/split", methods=["POST"])
def split_question(question_id):
    data = request.get_json(silent=True) or {}
    provider = data.get("provider", LLM_PROVIDER)
    model = data.get("model", LLM_MODEL)

    question = Question.query.get_or_404(question_id)

    if question.status not in (QuestionStatus.PENDING, QuestionStatus.PROCESSING):
        return jsonify({"error": "question cannot be split in its current state"}), 409

    if not LLM_SPLIT_ENABLED:
        return jsonify({"error": "LLM splitting is disabled"}), 400

    try:
        from llm import split_scene

        style = question.style or "fantasy art"
        layers = split_scene(question.description, style=style, provider=provider, model=model)

        if not layers:
            return jsonify({"error": "LLM failed to split the scene"}), 500

        if question.status == QuestionStatus.PENDING:
            question.status = QuestionStatus.PROCESSING

        for layer_data in layers:
            task = Task(
                question_id=question.id,
                type=question.type,
                depth=0,
                max_depth=question.max_depth,
                layer_number=layer_data["layer"],
                prompt=layer_data["prompt"],
                negative_prompt=layer_data.get("negative_prompt"),
            )
            db.session.add(task)

        db.session.commit()
        return jsonify(question_to_dict(question))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/task", methods=["POST"])
def create_tasks():
    data = request.get_json(silent=True)
    if not data or "question_id" not in data or "tasks" not in data:
        return jsonify({"error": "question_id and tasks are required"}), 400

    question = Question.query.get_or_404(data["question_id"])

    if question.status not in (QuestionStatus.PENDING, QuestionStatus.PROCESSING):
        return jsonify({"error": "question is already completed or failed"}), 409

    if question.status == QuestionStatus.PENDING:
        question.status = QuestionStatus.PROCESSING

    created = []
    for t in data["tasks"]:
        task = Task(
            question_id=question.id,
            type=question.type,
            parent_task_id=t.get("parent_task_id"),
            depth=t.get("depth", 0),
            max_depth=t.get("max_depth", question.max_depth),
            layer_number=t.get("layer_number"),
            prompt=t.get("prompt", ""),
            negative_prompt=t.get("negative_prompt"),
            input_image=t.get("input_image"),
            retry_count=t.get("retry_count", 0),
        )
        db.session.add(task)
        created.append(task)

    db.session.commit()
    return jsonify(question_to_dict(question)), 201


@app.route("/api/tasks/batch", methods=["POST"])
def create_tasks_batch():
    data = request.get_json(silent=True)
    if not data or "tasks" not in data:
        return jsonify({"error": "tasks array is required"}), 400

    created = []
    for t in data["tasks"]:
        task = Task(
            question_id=t["question_id"],
            type=JobType(t.get("type", "ITG")),
            parent_task_id=t.get("parent_task_id"),
            depth=t.get("depth", 0),
            max_depth=t.get("max_depth", 2),
            prompt=t.get("prompt", ""),
            negative_prompt=t.get("negative_prompt"),
            input_image=t.get("input_image"),
            retry_count=t.get("retry_count", 0),
        )
        db.session.add(task)
        created.append(task)

    if created:
        question = Question.query.get(created[0].question_id)
        if question and question.status == QuestionStatus.PENDING:
            question.status = QuestionStatus.PROCESSING

    db.session.commit()
    return jsonify([task_to_dict(t) for t in created]), 201


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    status_filter = request.args.get("status", "pending")
    type_filter = request.args.get("type")
    depth_filter = request.args.get("depth")
    parent_filter = request.args.get("parent_task_id")

    query = Task.query

    if status_filter:
        try:
            query = query.filter(Task.status == TaskStatus(status_filter))
        except ValueError:
            query = query.filter(Task.status == status_filter)

    if type_filter:
        query = query.filter(Task.type == type_filter.upper())

    if depth_filter is not None:
        query = query.filter(Task.depth == int(depth_filter))

    if parent_filter is not None:
        query = query.filter(Task.parent_task_id == int(parent_filter))

    tasks = query.order_by(Task.created_at.asc()).all()
    return jsonify([task_to_dict(t) for t in tasks])


@app.route("/api/task/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task_to_dict(task))


@app.route("/api/task/<int:task_id>/claim", methods=["POST"])
def claim_task(task_id):
    data = request.get_json(silent=True) or {}
    worker_id = data.get("worker_id", "anonymous")

    task = Task.query.get_or_404(task_id)

    if task.status != TaskStatus.PENDING:
        return jsonify({"error": "task is not available"}), 409

    task.status = TaskStatus.CLAIMED
    task.worker_id = worker_id
    task.claimed_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(task_to_dict(task))


@app.route("/api/task/<int:task_id>/reset", methods=["POST"])
def reset_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.status not in (TaskStatus.CLAIMED, TaskStatus.PENDING):
        return jsonify({"error": "only claimed or pending tasks can be reset"}), 409

    task.retry_count = (task.retry_count or 0) + 1
    if task.retry_count >= 3:
        task.status = TaskStatus.FAILED
        db.session.commit()
        return jsonify({"id": task.id, "status": "failed", "retry_count": task.retry_count, "error": "max retries exceeded"})

    task.status = TaskStatus.PENDING
    task.worker_id = None
    task.claimed_at = None
    db.session.commit()

    return jsonify(task_to_dict(task))


@app.route("/api/task/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json(silent=True) or {}

    if "prompt" in data:
        task.prompt = data["prompt"]
    if "negative_prompt" in data:
        task.negative_prompt = data["negative_prompt"]
    if "input_image" in data:
        task.input_image = data["input_image"]
    if "status" in data:
        task.status = TaskStatus(data["status"])

    db.session.commit()
    return jsonify(task_to_dict(task))


@app.route("/api/task/<int:task_id>/children", methods=["GET"])
def get_task_children(task_id):
    task = Task.query.get_or_404(task_id)
    children = Task.query.filter_by(parent_task_id=task_id).order_by(Task.id).all()
    return jsonify([task_to_dict(c) for c in children])


@app.route("/api/task/<int:task_id>/zorder", methods=["PUT"])
def set_task_zorder(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json(silent=True) or {}

    layers = data.get("layers", [])
    task.quality_judgment = json_module.dumps({"z_order": layers})
    db.session.commit()
    return jsonify(task_to_dict(task))


@app.route("/api/task/<int:task_id>/result", methods=["POST"])
def submit_result(task_id):
    task = Task.query.get_or_404(task_id)

    if task.status != TaskStatus.CLAIMED:
        return jsonify({"error": "task is not claimed or already completed"}), 409

    images = request.files.getlist("images")
    if not images:
        images = [request.files["image"]] if "image" in request.files else []

    if not images:
        return jsonify({"error": "at least one image file is required"}), 400

    question = Question.query.get(task.question_id)
    temp_dir = ITG_TEMP if (question and question.type == JobType.ITG) else TTG_TEMP

    saved = []
    for i, file in enumerate(images):
        if file.filename == "" or not allowed_file(file.filename):
            continue
        suffix = f"_{i+1}" if len(images) > 1 else ""
        filename = secure_filename(f"task{task.id}{suffix}_{file.filename}")
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        saved.append(filename)

    task.status = TaskStatus.COMPLETED
    task.result_filename = ",".join(saved) if len(saved) > 1 else (saved[0] if saved else None)
    task.completed_at = datetime.now(timezone.utc)

    if data := request.form:
        if data.get("split_result_1"):
            task.split_result_1 = data["split_result_1"]
        if data.get("split_result_2"):
            task.split_result_2 = data["split_result_2"]
        if data.get("quality_judgment"):
            task.quality_judgment = data["quality_judgment"]

    db.session.commit()

    _auto_complete_question(question)

    return jsonify(task_to_dict(task))


def _auto_complete_question(question):
    if not question or question.status == QuestionStatus.COMPLETED:
        return
    direct_children = Task.query.filter_by(question_id=question.id, depth=0).all()
    if direct_children and all(t.status == TaskStatus.COMPLETED for t in direct_children):
        question.status = QuestionStatus.COMPLETED
        question.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        _cleanup_question(question.id)


@app.route("/api/question/<int:question_id>/complete", methods=["POST"])
def complete_question(question_id):
    question = Question.query.get_or_404(question_id)

    images = request.files.getlist("images")
    if not images:
        return jsonify({"error": "at least one final image is required"}), 400

    question_type = question.type.value if question.type else "TTG"
    final_dir = ITG_FINAL if question_type == "ITG" else TTG_FINAL

    for i, file in enumerate(images):
        if file.filename == "":
            continue
        filename = secure_filename(f"task{question.id}_layer_{i+1}_{file.filename}")
        filepath = os.path.join(final_dir, filename)
        file.save(filepath)

    question.status = QuestionStatus.COMPLETED
    question.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    _cleanup_question(question.id)

    return jsonify(question_to_dict(question))


def _cleanup_question(question_id):
    question = Question.query.get(question_id)
    if not question:
        return
    question_type = question.type.value if question.type else "TTG"
    temp_dir = ITG_TEMP if question_type == "ITG" else TTG_TEMP
    pattern = os.path.join(temp_dir, f"task{question_id}*")
    for f in glob.glob(pattern):
        try:
            os.remove(f)
        except OSError:
            pass
    pattern2 = os.path.join(temp_dir, f"*task{question_id}*")
    for f in glob.glob(pattern2):
        try:
            os.remove(f)
        except OSError:
            pass


@app.route("/api/question/<int:question_id>/cleanup", methods=["DELETE"])
def cleanup_question(question_id):
    _cleanup_question(question_id)
    return jsonify({"cleaned": question_id})


@app.route("/api/question/<int:question_id>/tree", methods=["GET"])
def get_question_tree(question_id):
    question = Question.query.get_or_404(question_id)
    all_tasks = Task.query.filter_by(question_id=question_id).order_by(Task.depth, Task.id).all()

    def build_tree(parent_id=None):
        return [
            {
                "task": task_to_dict(t),
                "children": build_tree(t.id),
            }
            for t in all_tasks if t.parent_task_id == parent_id
        ]

    return jsonify({
        "question": question_to_dict(question, include_tasks=False),
        "tree": build_tree(None),
    })


@app.route("/api/question/<int:question_id>/stats", methods=["GET"])
def get_question_stats(question_id):
    question = Question.query.get_or_404(question_id)
    tasks = Task.query.filter_by(question_id=question_id).all()

    return jsonify({
        "question_id": question_id,
        "status": question.status.value,
        "total_tasks": len(tasks),
        "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
        "claimed": sum(1 for t in tasks if t.status == TaskStatus.CLAIMED),
        "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
        "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
        "discarded": sum(1 for t in tasks if t.discarded),
        "good_layers": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED and not t.discarded),
        "max_depth_reached": max((t.depth or 0) for t in tasks) if tasks else 0,
    })


# ─── File Endpoints ───────────────────────────────────────────────────

@app.route("/api/files/<path:filename>")
def serve_file(filename):
    search_dirs = [ORIGINALS, TTG_TEMP, TTG_FINAL, ITG_TEMP, ITG_FINAL, OUTPUT_DIR]
    for d in search_dirs:
        filepath = os.path.join(d, filename)
        if os.path.exists(filepath):
            return send_from_directory(d, filename)
    return jsonify({"error": "file not found"}), 404


@app.route("/api/files/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "valid PNG file is required"}), 400

    task_id = request.form.get("task_id", "unknown")
    filename = secure_filename(f"task{task_id}_{file.filename}")
    filepath = os.path.join(ITG_TEMP, filename)
    file.save(filepath)

    return jsonify({
        "filename": filename,
        "path": filepath,
        "size_bytes": os.path.getsize(filepath),
    })


@app.route("/api/health", methods=["GET"])
def health():
    import shutil as sh
    disk = sh.disk_usage(OUTPUT_ROOT)
    return jsonify({
        "status": "ok",
        "disk_free_gb": round(disk.free / 1e9, 1),
        "disk_total_gb": round(disk.total / 1e9, 1),
        "active_questions": Question.query.filter(Question.status == QuestionStatus.PROCESSING).count(),
        "pending_questions": Question.query.filter(Question.status == QuestionStatus.PENDING).count(),
        "pending_tasks": Task.query.filter(Task.status == TaskStatus.PENDING).count(),
    })


@app.route("/api/health/llm", methods=["GET"])
def health_llm():
    provider = request.args.get("provider", LLM_PROVIDER)
    try:
        from llm import check_llm_health
        ok = check_llm_health(provider)
        return jsonify({"provider": provider, "available": ok})
    except Exception as e:
        return jsonify({"provider": provider, "available": False, "error": str(e)})


# ─── Legacy compatibility ─────────────────────────────────────────────

@app.route("/api/result/<filename>")
def serve_result(filename):
    return serve_file(filename)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
