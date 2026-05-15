from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.models import SlotSignup, User, VideoSession
from src.backend.app.schemas import BroadcastSessionRead
from src.backend.app.services.video_curator import record_cache_play


@dataclass
class BroadcastState:
    video_session_id: int
    started_at: datetime
    started_by_user_id: int
    joined_user_ids: set[int] = field(default_factory=set)
    exited_user_ids: set[int] = field(default_factory=set)


_broadcast_sessions: dict[int, BroadcastState] = {}
_broadcast_lock = Lock()


def clear_broadcast_sessions() -> None:
    with _broadcast_lock:
        _broadcast_sessions.clear()


def start_or_join_broadcast(
    db: Session,
    current_user: User,
    video_session_id: int,
) -> BroadcastSessionRead:
    video_session = get_member_video_session(db, current_user, video_session_id)

    with _broadcast_lock:
        state = _broadcast_sessions.get(video_session.id)
        if state is not None and not state.joined_user_ids:
            state = None
            _broadcast_sessions.pop(video_session.id, None)

        if state is None:
            state = BroadcastState(
                video_session_id=video_session.id,
                started_at=datetime.now(UTC),
                started_by_user_id=current_user.id,
            )
            _broadcast_sessions[video_session.id] = state
            record_cache_play(db, video_session.youtube_video_id)
            db.commit()

        if current_user.id in state.exited_user_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You exited this broadcast session and cannot rejoin it.",
            )

        state.joined_user_ids.add(current_user.id)
        return serialize_broadcast_state(state, video_session)


def read_broadcast(
    db: Session,
    current_user: User,
    video_session_id: int,
) -> BroadcastSessionRead:
    video_session = get_member_video_session(db, current_user, video_session_id)
    state = _broadcast_sessions.get(video_session.id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broadcast session has not started.",
        )
    return serialize_broadcast_state(state, video_session)


def exit_broadcast(db: Session, current_user: User, video_session_id: int) -> BroadcastSessionRead:
    video_session = get_member_video_session(db, current_user, video_session_id)

    with _broadcast_lock:
        state = _broadcast_sessions.get(video_session.id)
        if state is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broadcast session has not started.",
            )

        state.joined_user_ids.discard(current_user.id)
        state.exited_user_ids.add(current_user.id)
        return serialize_broadcast_state(state, video_session)


def get_member_video_session(db: Session, current_user: User, video_session_id: int) -> VideoSession:
    video_session = db.get(VideoSession, video_session_id)
    if video_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session was not found.",
        )

    reservation = db.scalar(
        select(SlotSignup).where(
            SlotSignup.user_id == current_user.id,
            SlotSignup.time_slot_id == video_session.time_slot_id,
            SlotSignup.workout_category_id == video_session.workout_category_id,
        )
    )
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A matching reservation is required to join this broadcast.",
        )

    return video_session


def serialize_broadcast_state(
    state: BroadcastState,
    video_session: VideoSession,
) -> BroadcastSessionRead:
    now = datetime.now(UTC)
    elapsed_seconds = max(0, int((now - state.started_at).total_seconds()))
    duration_seconds = video_session.duration_seconds or 0
    if duration_seconds > 0:
        elapsed_seconds = min(elapsed_seconds, duration_seconds)

    return BroadcastSessionRead(
        video_session_id=state.video_session_id,
        time_slot_id=video_session.time_slot_id,
        workout_category_id=video_session.workout_category_id,
        started_at=state.started_at,
        server_time=now,
        playback_offset_seconds=elapsed_seconds,
        duration_seconds=video_session.duration_seconds,
        participant_count=len(state.joined_user_ids),
        exited_participant_count=len(state.exited_user_ids),
        status=(
            "ended"
            if not state.joined_user_ids or (duration_seconds > 0 and elapsed_seconds >= duration_seconds)
            else "active"
        ),
    )
