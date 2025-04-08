from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime, UTC
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class APIKeyRotationHistory(Base):
    """
    Model for tracking API key rotation history.
    This maintains a record of all key rotations for audit and security purposes.
    """
    __tablename__ = "api_key_rotation_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    api_key_id = Column(String, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    previous_key_id = Column(String, nullable=True)
    previous_prefix = Column(String, nullable=True)
    rotation_date = Column(DateTime, default=lambda: datetime.now(UTC))
    reason = Column(String, nullable=False)  # 'regular', 'compromised', 'expired'
    rotated_by_user_id = Column(String, nullable=True)  # user ID who initiated the rotation
    grace_period_days = Column(Integer, nullable=True)
    grace_period_end = Column(DateTime, nullable=True)
    is_compromised = Column(Boolean, default=False)  # Whether the key was rotated due to compromise
    
    # Relationships
    api_key = relationship("APIKey", back_populates="rotation_history")
    
    def __repr__(self):
        return f"<APIKeyRotationHistory(id={self.id}, api_key_id={self.api_key_id}, rotation_date={self.rotation_date})>"
