import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_sub = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    avatar_url = Column(String)
    
    plan = Column(String(20), default="free")
    scan_count = Column(Integer, default=0)
    scan_reset_at = Column(DateTime)
    subscription_end = Column(DateTime)
    razorpay_customer_id = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)