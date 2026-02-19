from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # LinkedIn credentials (encrypted)
    linkedin_email = Column(Text)  # Encrypted
    linkedin_password = Column(Text)  # Encrypted
    linkedin_session = Column(Text)  # Encrypted cookies/session
    
    # LLM config (encrypted)
    llm_config_encrypted = Column(Text, nullable=False)
    
    # Automation settings
    automation_enabled = Column(Boolean, default=True)
    daily_limits = Column(JSON, default={})  # {connections: 50, messages: 30}
    
    # Preferences
    preferences = Column(JSON, default={})
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    campaigns = relationship("Campaign", back_populates="user")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="active")  # active, paused, completed
    
    # Target filters
    target_filters = Column(JSON, nullable=False)
    
    # Message sequence
    sequence = Column(JSON, nullable=False)  # [{day: 0, action: "connect", template: "..."}]
    
    # Stats
    stats = Column(JSON, default={})  # {sent: 0, accepted: 0, replied: 0}
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="campaigns")
    prospects = relationship("Prospect", back_populates="campaign")


class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prospect_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    campaign_id = Column(String(255), ForeignKey("campaigns.campaign_id"))
    
    # LinkedIn data
    linkedin_url = Column(Text, nullable=False)
    full_name = Column(String(255))
    headline = Column(String(500))
    company = Column(String(255))
    title = Column(String(255))
    location = Column(String(255))
    
    # AI scoring
    ai_score = Column(Integer)  # 1-10
    score_reasoning = Column(Text)
    
    # Status
    stage = Column(String(50), default="new")  # new, contacted, connected, replied, cold
    connection_status = Column(String(50))  # pending, accepted, not_sent
    
    # Conversation
    conversation_history = Column(JSON, default=[])
    
    last_interaction_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    campaign = relationship("Campaign", back_populates="prospects")


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    prospect_id = Column(String(255), ForeignKey("prospects.prospect_id"))
    campaign_id = Column(String(255), ForeignKey("campaigns.campaign_id"))
    
    # Action details
    action_type = Column(String(50), nullable=False)  # connect, message, visit_profile
    action_data = Column(JSON, nullable=False)
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=False)
    executed_at = Column(DateTime)
    
    # Status
    status = Column(String(50), default="pending")  # pending, executing, completed, failed
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
