from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SAEnum
import enum

db = SQLAlchemy()


class QuestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    COMPLETED = "completed"


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    style = db.Column(db.String(128), nullable=True)
    status = db.Column(
        SAEnum(QuestionStatus),
        default=QuestionStatus.PENDING,
        nullable=False,
    )
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
    layer_number = db.Column(db.Integer, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    negative_prompt = db.Column(db.Text, nullable=True)
    status = db.Column(
        SAEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    worker_id = db.Column(db.String(64), nullable=True)
    result_filename = db.Column(db.String(256), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    claimed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    question = db.relationship("Question", back_populates="tasks")
