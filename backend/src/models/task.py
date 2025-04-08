from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from enum import Enum
from ..core.database import Base  # Import Base directly from database

class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    type = Column(String, nullable=False)
    status = Column(String, default=TaskStatus.QUEUED)
    result_url = Column(String)
    created_at = Column(DateTime, default=func.now())

    def __init__(self, user_id: str, type: str):
        self.user_id = user_id
        self.type = type
        self.status = TaskStatus.QUEUED

    def __repr__(self):
        return f"<Task(id={self.id}, type={self.type}, status={self.status})>"