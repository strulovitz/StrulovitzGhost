import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

from config import DATABASE_URL, SECRET_KEY, OUTPUT_DIR, LLM_PROVIDER, LLM_MODEL, LLM_SPLIT_ENABLED
from models import db, Question, Task, QuestionStatus, TaskStatus

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


ALLOWED_EXTENSIONS = {"png"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def question_to_dict(q):
    return {
        "id": q.id,
        "description": q.description,
        "style": q.style,
        "status": q.status.value,
        "created_at": q.created_at.isoformat(),
        "completed_at": q.completed_at.isoformat() if q.completed_at else None,
        "tasks": [
            {
                "id": t.id,
                "layer_number": t.layer_number,
                "prompt": t.prompt,
                "status": t.status.value,
                "worker_id": t.worker_id,
                "result_filename": t.result_filename,
                "created_at": t.created_at.isoformat(),
                "claimed_at": t.claimed_at.isoformat() if t.claimed_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in q.tasks
        ],
    }


@app.route("/")
def index():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template("index.html", questions=questions)


@app.route("/api/question", methods=["POST"])
def submit_question():
    data = request.get_json(silent=True)
    if not data or "description" not in data:
        return jsonify({"error": "description is required"}), 400

    question = Question(
        description=data["description"],
        style=data.get("style", None),
    )
    db.session.add(question)
    db.session.commit()
    return jsonify(question_to_dict(question)), 201


@app.route("/api/questions", methods=["GET"])
def list_questions():
    status_filter = request.args.get("status")
    query = Question.query
    if status_filter:
        query = query.filter(Question.status == status_filter)
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
                layer_number=layer_data["layer"],
                prompt=layer_data["prompt"],
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

    if question.status != QuestionStatus.PENDING:
        return jsonify({"error": "question is already being processed"}), 409

    question.status = QuestionStatus.PROCESSING

    created = []
    for t in data["tasks"]:
        task = Task(
            question_id=question.id,
            layer_number=t["layer_number"],
            prompt=t["prompt"],
        )
        db.session.add(task)
        created.append(task)

    db.session.commit()
    return jsonify(question_to_dict(question)), 201


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    status_filter = request.args.get("status", "pending")
    tasks = (
        Task.query.filter(Task.status == status_filter)
        .order_by(Task.created_at.asc())
        .all()
    )
    return jsonify(
        [
            {
                "id": t.id,
                "layer_number": t.layer_number,
                "prompt": t.prompt,
                "status": t.status.value,
            }
            for t in tasks
        ]
    )


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

    return jsonify(
        {
            "id": task.id,
            "layer_number": task.layer_number,
            "prompt": task.prompt,
            "status": task.status.value,
            "worker_id": task.worker_id,
        }
    )


@app.route("/api/task/<int:task_id>/result", methods=["POST"])
def submit_result(task_id):
    task = Task.query.get_or_404(task_id)

    if task.status != TaskStatus.CLAIMED:
        return jsonify({"error": "task is not claimed or already completed"}), 409

    if "image" not in request.files:
        return jsonify({"error": "image file is required"}), 400

    file = request.files["image"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "valid PNG file is required"}), 400

    filename = secure_filename(f"layer{task.layer_number}_task{task.id}_{file.filename}")
    filepath = os.path.join(OUTPUT_DIR, filename)
    file.save(filepath)

    task.status = TaskStatus.COMPLETED
    task.result_filename = filename
    task.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    question = Question.query.get(task.question_id)
    all_completed = all(t.status == TaskStatus.COMPLETED for t in question.tasks)
    if all_completed:
        question.status = QuestionStatus.COMPLETED
        question.completed_at = datetime.now(timezone.utc)
        db.session.commit()

    return jsonify(
        {
            "id": task.id,
            "status": task.status.value,
            "result_filename": task.result_filename,
        }
    )


@app.route("/api/result/<filename>")
def serve_result(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
