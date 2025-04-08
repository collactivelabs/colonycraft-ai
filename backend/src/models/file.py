# src/models/file.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from .base import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))  # Links the file to a user
    file_url = Column(String, nullable=False)  # URL of the generated file
    type = Column(String, nullable=False)  # Type of file (e.g., "image", "video")
    created_at = Column(DateTime, default=func.now())  # Timestamp of file creation