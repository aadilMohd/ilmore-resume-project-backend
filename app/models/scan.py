import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    resume_hash = Column(String(64), index=True)
    resume_storage_path = Column(String)
    jd_text = Column(String, nullable=False)
    
    # JSONB is a special Postgres type that makes storing and querying JSON incredibly fast
    gemini_result = Column(JSONB)
    claude_result = Column(JSONB)
    
    match_score_gemini = Column(Integer)
    match_score_claude = Column(Integer)
    
    user_feedback = Column(String(20))
    user_preferred_ai = Column(String(10))
    processing_time_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)