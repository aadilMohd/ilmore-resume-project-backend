import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_sub = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    avatar_url = Column(String)
    plan = Column(Enum('free', 'student', 'pro', name='plan_types'), default='free')
    scan_count = Column(Integer, default=0)
    scan_reset_at = Column(DateTime)
    subscription_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("Scan", back_populates="user")

class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resume_text = Column(String)
    jd_text = Column(String)
    gemini_result = Column(JSON)
    claude_result = Column(JSON)
    match_score_gemini = Column(Integer)
    match_score_claude = Column(Integer)
    user_feedback = Column(Enum('helpful', 'not_helpful', name='feedback_types'), nullable=True)
    user_preferred_ai = Column(Enum('gemini', 'claude', name='preferred_ai_types'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scans")