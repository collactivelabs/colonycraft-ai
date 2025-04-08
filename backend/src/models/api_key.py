from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, ARRAY, JSON, Integer
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime, UTC
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    prefix = Column(String(8), nullable=False, index=True, unique=True)
    key_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scopes = Column(JSON, nullable=False, default=lambda: ["*"])
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Rotation-related fields
    rotated_from_id = Column(String, ForeignKey("api_keys.id"), nullable=True)
    rotation_date = Column(DateTime, nullable=True)
    grace_period_days = Column(Integer, nullable=True)
    grace_period_end = Column(DateTime, nullable=True)
    was_compromised = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", overlaps="api_keys")
    rotation_history = relationship("APIKeyRotationHistory", back_populates="api_key", cascade="all, delete-orphan")
    
    # Self-reference for tracking rotated keys
    previous_key = relationship("APIKey", remote_side=[id], foreign_keys=[rotated_from_id], backref="rotated_to", uselist=False)
    
    def is_valid(self):
        """Check if the API key is still valid"""
        if not self.is_active:
            return False
        
        # Check if the key has expired
        if self.expires_at and self.expires_at < datetime.now(UTC):
            return False
            
        return True
        
    def update_last_used(self):
        """Update the last used timestamp"""
        self.last_used_at = datetime.now(UTC)
        
    def is_in_grace_period(self):
        """Check if the key is in its grace period after rotation"""
        if not self.grace_period_end:
            return False
        
        return self.grace_period_end > datetime.now(UTC)
