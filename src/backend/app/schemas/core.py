from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiStatus(BaseModel):
    status: str
    phase: str
    message: str
    ai_llm_provider: str
    ai_recommender_mode: str
    mock_fallback_enabled: bool
    debug_enabled: bool


class TimeSlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    start_hour: int
    end_hour: int
    capacity: int
    is_active: bool
    is_demo: bool
    current_occupancy: int


class WorkoutCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    is_active: bool


class VideoSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    time_slot_id: int
    workout_category_id: int
    title: str | None
    youtube_video_id: str | None
    youtube_url: str | None
    duration_seconds: int | None
    provider: str
    status: str
    safety_notes: str | None
    agent_summary: str | None


class VideoCacheEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_category_id: int
    title: str
    youtube_video_id: str
    youtube_url: str
    duration_seconds: int
    provider: str
    status: str
    play_count: int
    safety_notes: str | None
    curator_summary: str | None
    last_played_at: datetime | None
    confirmed_at: datetime | None


class VideoCuratorRunRead(BaseModel):
    created_pending: int
    categories: int


class VideoRecommendationRequest(BaseModel):
    time_slot_id: int = Field(gt=0)
    workout_category_id: int = Field(gt=0)


class VideoPlaybackFailure(BaseModel):
    failed_video_id: str | None = None
    reason: str | None = None


class VideoPlaybackConfirmed(BaseModel):
    youtube_video_id: str | None = None


class BroadcastSessionCreate(BaseModel):
    video_session_id: int = Field(gt=0)


class BroadcastSessionRead(BaseModel):
    video_session_id: int
    time_slot_id: int
    workout_category_id: int
    started_at: datetime
    server_time: datetime
    playback_offset_seconds: int
    duration_seconds: int | None
    participant_count: int
    exited_participant_count: int
    status: str


class FeedbackCreate(BaseModel):
    video_session_id: int = Field(gt=0)
    value: Literal["like", "dislike"]


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    video_session_id: int
    value: str
    created_at: datetime


class FeedbackSummaryRead(BaseModel):
    video_session_id: int
    title: str | None
    time_slot_id: int
    workout_category_id: int
    likes: int
    dislikes: int
    total_feedback: int
    score: int


class ReservationCreate(BaseModel):
    time_slot_id: int = Field(gt=0)
    workout_category_id: int = Field(gt=0)


class UserStatusUpdate(BaseModel):
    is_active: bool


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    time_slot_id: int
    workout_category_id: int
    created_at: datetime


class OccupancyRead(BaseModel):
    time_slot_id: int
    label: str
    start_hour: int
    end_hour: int
    capacity: int
    current_occupancy: int
    remaining_capacity: int
    is_full: bool
    is_demo: bool
