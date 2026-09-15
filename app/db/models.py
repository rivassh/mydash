"""Database models using SQLAlchemy 2.0 ORM."""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class SourceType(PyEnum):
    BALE = "bale"


class MessageDirection(PyEnum):
    IN = "in"
    OUT = "out"


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="source", lazy="dynamic")
    sync_state = relationship("SyncState", back_populates="source", uselist=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    remote_conversation_id = Column(String(255), nullable=False)
    title = Column(String(500))
    avatar_url = Column(String(1000))
    last_message_at = Column(DateTime)
    last_message_preview = Column(String(500))
    unread_count = Column(Integer, default=0, nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    pinned = Column(Boolean, default=False, nullable=False)
    sync_updated_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("source_id", "remote_conversation_id", name="uq_conv_source_remote"),
        Index("ix_conv_source_last_msg", "source_id", "last_message_at"),
    )

    source = relationship("Source", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", lazy="dynamic")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    source_message_id = Column(String(255), nullable=False)
    direction = Column(String(10), nullable=False)  # 'in' or 'out'
    sender_name = Column(String(255))
    body_text = Column(Text, nullable=False)
    body_type = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(50))

    __table_args__ = (
        UniqueConstraint("conversation_id", "source_message_id", name="uq_msg_conv_source"),
        Index("ix_msg_conv_created", "conversation_id", "created_at"),
    )

    conversation = relationship("Conversation", back_populates="messages")


class SyncState(Base):
    __tablename__ = "sync_state"

    source_id = Column(Integer, ForeignKey("sources.id"), primary_key=True)
    cursor = Column(Text, nullable=False, default="")
    last_success_at = Column(DateTime)
    last_error_at = Column(DateTime)
    last_error_msg = Column(Text)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = relationship("Source", back_populates="sync_state")


class Draft(Base):
    """Placeholder for Phase 3+."""
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    body_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class OutboxQueue(Base):
    """Placeholder for Phase 3+."""
    __tablename__ = "outbox_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    source_message_id = Column(String(255))
    body_text = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime)