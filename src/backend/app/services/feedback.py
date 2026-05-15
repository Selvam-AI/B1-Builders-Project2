from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.app.models import Feedback, SlotSignup, User, VideoSession
from src.backend.app.schemas import FeedbackCreate, FeedbackSummaryRead


def create_or_update_feedback(db: Session, user: User, payload: FeedbackCreate) -> Feedback:
    video_session = db.get(VideoSession, payload.video_session_id)
    if video_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session was not found.",
        )

    reservation = db.scalar(
        select(SlotSignup).where(
            SlotSignup.user_id == user.id,
            SlotSignup.time_slot_id == video_session.time_slot_id,
            SlotSignup.workout_category_id == video_session.workout_category_id,
        )
    )
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Feedback requires a matching reservation.",
        )

    feedback = db.scalar(
        select(Feedback).where(
            Feedback.user_id == user.id,
            Feedback.video_session_id == video_session.id,
        )
    )
    if feedback is None:
        feedback = Feedback(
            user_id=user.id,
            video_session_id=video_session.id,
            value=payload.value,
        )
        db.add(feedback)
    else:
        feedback.value = payload.value

    db.commit()
    db.refresh(feedback)
    return feedback


def list_feedback_summaries(db: Session) -> list[FeedbackSummaryRead]:
    sessions = db.scalars(select(VideoSession).order_by(VideoSession.id)).all()
    summaries: list[FeedbackSummaryRead] = []

    for session in sessions:
        likes = feedback_count(db, session.id, "like")
        dislikes = feedback_count(db, session.id, "dislike")
        total = likes + dislikes
        summaries.append(
            FeedbackSummaryRead(
                video_session_id=session.id,
                title=session.title,
                time_slot_id=session.time_slot_id,
                workout_category_id=session.workout_category_id,
                likes=likes,
                dislikes=dislikes,
                total_feedback=total,
                score=likes - dislikes,
            )
        )

    return summaries


def feedback_count(db: Session, video_session_id: int, value: str) -> int:
    return (
        db.scalar(
            select(func.count(Feedback.id)).where(
                Feedback.video_session_id == video_session_id,
                Feedback.value == value,
            )
        )
        or 0
    )
