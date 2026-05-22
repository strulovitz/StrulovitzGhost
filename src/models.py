from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SAEnum
import enum

db = SQLAlchemy()


class JobType(str, enum.Enum):
    TTG = "TTG"
    ITG = "ITG"


class QuestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    FAILED = "failed"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(SAEnum(JobType), default=JobType.TTG, nullable=False)
    description = db.Column(db.Text, nullable=True)
    style = db.Column(db.String(128), nullable=True)
    status = db.Column(
        SAEnum(QuestionStatus),
        default=QuestionStatus.PENDING,
        nullable=False,
    )
    global_negative_prompt = db.Column(db.Text, nullable=True)
    input_image_path = db.Column(db.String(512), nullable=True)
    input_image_url = db.Column(db.String(1024), nullable=True)
    original_resolution = db.Column(db.String(32), nullable=True)
    max_depth = db.Column(db.Integer, default=0)
    depth_control_manual = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = db.Column(db.DateTime, nullable=True)

    tasks = db.relationship("Task", back_populates="question", order_by="Task.layer_number")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    type = db.Column(SAEnum(JobType), default=JobType.TTG, nullable=False)
    parent_task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True)
    depth = db.Column(db.Integer, default=0)
    max_depth = db.Column(db.Integer, default=0)
    layer_number = db.Column(db.Integer, nullable=True)
    prompt = db.Column(db.Text, nullable=True)
    negative_prompt = db.Column(db.Text, nullable=True)
    status = db.Column(
        SAEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    worker_id = db.Column(db.String(64), nullable=True)
    result_filename = db.Column(db.String(512), nullable=True)
    input_image = db.Column(db.String(512), nullable=True)
    split_result_1 = db.Column(db.String(512), nullable=True)
    split_result_2 = db.Column(db.String(512), nullable=True)
    quality_judgment = db.Column(db.Text, nullable=True)
    z_order = db.Column(db.Integer, nullable=True)
    discarded = db.Column(db.Boolean, default=False)
    retry_count = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    claimed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    question = db.relationship("Question", back_populates="tasks")
    children = db.relationship("Task", backref=db.backref("parent", remote_side=[id]), order_by="Task.id")
