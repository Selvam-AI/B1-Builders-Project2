from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    preferred_time_slots: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    signups: Mapped[list["SlotSignup"]] = relationship(back_populates="user")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="user")


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    label: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    start_hour: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    end_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    signups: Mapped[list["SlotSignup"]] = relationship(back_populates="time_slot")
    video_sessions: Mapped[list["VideoSession"]] = relationship(back_populates="time_slot")


class WorkoutCategory(Base):
    __tablename__ = "workout_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    video_sessions: Mapped[list["VideoSession"]] = relationship(back_populates="category")
    video_cache_entries: Mapped[list["VideoCacheEntry"]] = relationship(back_populates="category")


class VideoCacheEntry(Base):
    __tablename__ = "video_cache_entries"
    __table_args__ = (UniqueConstraint("youtube_video_id", name="uq_video_cache_youtube_video_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workout_category_id: Mapped[int] = mapped_column(ForeignKey("workout_categories.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    youtube_video_id: Mapped[str] = mapped_column(String(80), nullable=False)
    youtube_url: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="youtube", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending_playback", nullable=False)
    play_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    curator_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_played_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    category: Mapped["WorkoutCategory"] = relationship(back_populates="video_cache_entries")


class SlotSignup(Base):
    __tablename__ = "slot_signups"
    __table_args__ = (UniqueConstraint("user_id", "time_slot_id", name="uq_user_slot_signup"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"), nullable=False)
    workout_category_id: Mapped[int] = mapped_column(ForeignKey("workout_categories.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="signups")
    time_slot: Mapped["TimeSlot"] = relationship(back_populates="signups")
    category: Mapped["WorkoutCategory"] = relationship()


class VideoSession(Base):
    __tablename__ = "video_sessions"
    __table_args__ = (
        UniqueConstraint("time_slot_id", "workout_category_id", name="uq_video_session_slot_category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"), nullable=False)
    workout_category_id: Mapped[int] = mapped_column(ForeignKey("workout_categories.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider: Mapped[str] = mapped_column(String(40), default="mock", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    time_slot: Mapped["TimeSlot"] = relationship(back_populates="video_sessions")
    category: Mapped["WorkoutCategory"] = relationship(back_populates="video_sessions")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="video_session")


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("user_id", "video_session_id", name="uq_user_video_feedback"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    video_session_id: Mapped[int] = mapped_column(ForeignKey("video_sessions.id"), nullable=False)
    value: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="feedback")
    video_session: Mapped["VideoSession"] = relationship(back_populates="feedback")
