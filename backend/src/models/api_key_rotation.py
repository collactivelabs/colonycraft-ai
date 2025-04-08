from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class APIKeyRotationHistory(Base):
    """Tracks the history of API key rotations for audit and security purposes"""
    __tablename__ = "api_key_rotation_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    api_key_id = Column(String, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    previous_prefix = Column(String(8), nullable=False)
    rotation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    rotated_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=True)
    grace_period_days = Column(Integer, nullable=True)
    grace_period_end = Column(DateTime, nullable=True)
    is_compromised = Column(Boolean, default=False)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="rotation_history")
    rotated_by = relationship("User")
    
    def __repr__(self):
        return f"<APIKeyRotationHistory(id={self.id}, api_key_id={self.api_key_id}, rotation_date={self.rotation_date})>"
