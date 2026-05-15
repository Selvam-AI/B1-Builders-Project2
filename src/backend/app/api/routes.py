from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.core.database import get_db
from src.backend.app.core.security import get_current_user, require_admin, require_member
from src.backend.app.models import (
    Feedback,
    SlotSignup,
    TimeSlot,
    User,
    VideoCacheEntry,
    VideoSession,
    WorkoutCategory,
)
from src.backend.app.schemas import (
    ApiStatus,
    BroadcastSessionCreate,
    BroadcastSessionRead,
    FeedbackCreate,
    FeedbackRead,
    FeedbackSummaryRead,
    LoginRequest,
    MemberRegister,
    OccupancyRead,
    ReservationCreate,
    ReservationRead,
    TimeSlotRead,
    TokenResponse,
    UserRead,
    UserStatusUpdate,
    VideoCacheEntryRead,
    VideoCuratorRunRead,
    VideoPlaybackConfirmed,
    VideoPlaybackFailure,
    VideoRecommendationRequest,
    VideoSessionRead,
    WorkoutCategoryRead,
)
from src.backend.app.services.auth import authenticate_user, create_member, issue_token, serialize_user
from src.backend.app.services.broadcasts import (
    exit_broadcast,
    get_member_video_session,
    read_broadcast,
    start_or_join_broadcast,
)
from src.backend.app.services.feedback import create_or_update_feedback, list_feedback_summaries
from src.backend.app.services.recommendations import (
    confirm_video_playback,
    get_or_create_video_recommendation,
    replace_failed_video_recommendation,
)
from src.backend.app.services.scheduling import (
    cancel_reservation,
    create_reservation,
    list_member_reservations,
    list_slot_occupancy,
)
from src.backend.app.services.video_curator import maintain_video_cache

router = APIRouter()


@router.get("/status", response_model=ApiStatus)
async def api_status() -> ApiStatus:
    return ApiStatus(
        status="ok",
        phase="phase-8-video-curator",
        message="FitHub AI backend deterministic video curator is ready.",
        ai_llm_provider=settings.ai_llm_provider,
        ai_recommender_mode=settings.ai_recommender_mode,
        mock_fallback_enabled=settings.ai_allow_mock_fallback,
        debug_enabled=settings.debug,
    )


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register_member(
    payload: MemberRegister,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = create_member(db, payload)
    return issue_token(user)


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    return issue_token(user)


@router.get("/auth/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    return serialize_user(current_user)


@router.get("/admin/summary")
async def admin_summary(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> dict[str, int | str]:
    return {
        "admin": current_admin.email or current_admin.name,
        "members": db.scalar(select(func.count(User.id)).where(User.role == "member")) or 0,
        "time_slots": db.scalar(select(func.count(TimeSlot.id))) or 0,
        "video_sessions": db.scalar(select(func.count(VideoSession.id))) or 0,
    }


@router.get("/admin/occupancy", response_model=list[OccupancyRead])
async def admin_occupancy(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> list[OccupancyRead]:
    return list_slot_occupancy(db)


@router.get("/admin/feedback-summary", response_model=list[FeedbackSummaryRead])
async def admin_feedback_summary(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> list[FeedbackSummaryRead]:
    return list_feedback_summaries(db)


@router.get("/admin/video-cache", response_model=list[VideoCacheEntryRead])
async def admin_video_cache(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> list[VideoCacheEntry]:
    return list(
        db.scalars(
            select(VideoCacheEntry).order_by(
                VideoCacheEntry.workout_category_id,
                VideoCacheEntry.status,
                VideoCacheEntry.play_count,
                VideoCacheEntry.id,
            )
        ).all()
    )


@router.post("/admin/video-cache/curate", response_model=VideoCuratorRunRead)
async def admin_run_video_curator(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> VideoCuratorRunRead:
    return VideoCuratorRunRead(**maintain_video_cache(db))


@router.get("/admin/users", response_model=list[UserRead])
async def admin_users(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> list[UserRead]:
    users = db.scalars(
        select(User).where(User.role != "admin").order_by(User.created_at.desc(), User.id.desc())
    ).all()
    return [serialize_user(user) for user in users]


@router.patch("/admin/users/{user_id}/status", response_model=UserRead)
async def admin_update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> UserRead:
    user = db.get(User, user_id)
    if user is None or user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member account was not found.",
        )

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.delete("/admin/users/{user_id}", status_code=204)
async def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
) -> None:
    user = db.get(User, user_id)
    if user is None or user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member account was not found.",
        )

    db.query(Feedback).filter(Feedback.user_id == user.id).delete(synchronize_session=False)
    db.query(SlotSignup).filter(SlotSignup.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()


@router.post("/reservations", response_model=ReservationRead, status_code=201)
async def reserve_slot(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> SlotSignup:
    return create_reservation(db, current_member, payload)


@router.get("/reservations/me", response_model=list[ReservationRead])
async def my_reservations(
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> list[SlotSignup]:
    return list_member_reservations(db, current_member)


@router.delete("/reservations/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> None:
    cancel_reservation(db, current_member, reservation_id)


@router.post("/feedback", response_model=FeedbackRead)
async def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> FeedbackRead:
    return create_or_update_feedback(db, current_member, payload)


@router.post("/video-sessions/recommend", response_model=VideoSessionRead)
async def recommend_video_session(
    payload: VideoRecommendationRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> VideoSession:
    return get_or_create_video_recommendation(
        db,
        payload.time_slot_id,
        payload.workout_category_id,
    )


@router.post("/video-sessions/{video_session_id}/replace", response_model=VideoSessionRead)
async def replace_video_session(
    video_session_id: int,
    payload: VideoPlaybackFailure,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> VideoSession:
    video_session = get_member_video_session(db, current_member, video_session_id)
    return replace_failed_video_recommendation(
        db,
        video_session,
        failed_video_id=payload.failed_video_id,
        reason=payload.reason,
    )


@router.post("/video-sessions/{video_session_id}/playable", response_model=VideoSessionRead)
async def confirm_video_session_playback(
    video_session_id: int,
    payload: VideoPlaybackConfirmed,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> VideoSession:
    video_session = get_member_video_session(db, current_member, video_session_id)
    return confirm_video_playback(db, video_session, payload.youtube_video_id)


@router.post("/broadcast-sessions/start", response_model=BroadcastSessionRead)
async def start_broadcast_session(
    payload: BroadcastSessionCreate,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> BroadcastSessionRead:
    return start_or_join_broadcast(db, current_member, payload.video_session_id)


@router.get("/broadcast-sessions/{video_session_id}", response_model=BroadcastSessionRead)
async def get_broadcast_session(
    video_session_id: int,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> BroadcastSessionRead:
    return read_broadcast(db, current_member, video_session_id)


@router.post("/broadcast-sessions/{video_session_id}/exit", response_model=BroadcastSessionRead)
async def exit_broadcast_session(
    video_session_id: int,
    db: Session = Depends(get_db),
    current_member: User = Depends(require_member),
) -> BroadcastSessionRead:
    return exit_broadcast(db, current_member, video_session_id)


@router.get("/time-slots", response_model=list[TimeSlotRead])
async def list_time_slots(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[TimeSlotRead]:
    occupancy_counts = dict(
        db.execute(
            select(SlotSignup.time_slot_id, func.count(SlotSignup.id)).group_by(
                SlotSignup.time_slot_id
            )
        ).all()
    )
    slots = db.scalars(select(TimeSlot).order_by(TimeSlot.start_hour)).all()
    return [
        TimeSlotRead(
            id=slot.id,
            label=slot.label,
            start_hour=slot.start_hour,
            end_hour=slot.end_hour,
            capacity=slot.capacity,
            is_active=slot.is_active,
            is_demo=slot.is_demo,
            current_occupancy=occupancy_counts.get(slot.id, 0),
        )
        for slot in slots
    ]


@router.get("/workout-categories", response_model=list[WorkoutCategoryRead])
async def list_workout_categories(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[WorkoutCategory]:
    return list(
        db.scalars(
            select(WorkoutCategory)
            .where(WorkoutCategory.is_active.is_(True))
            .order_by(WorkoutCategory.id)
        ).all()
    )


@router.get("/video-sessions", response_model=list[VideoSessionRead])
async def list_video_sessions(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[VideoSession]:
    return list(db.scalars(select(VideoSession).order_by(VideoSession.id)).all())
