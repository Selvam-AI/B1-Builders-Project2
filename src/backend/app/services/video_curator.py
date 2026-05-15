from datetime import UTC, datetime
from threading import Event, Thread

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.core.database import SessionLocal
from src.backend.app.models import VideoCacheEntry, VideoSession, WorkoutCategory


_curator_stop_event = Event()
_curator_thread: Thread | None = None


def select_cached_candidate(
    db: Session,
    category: WorkoutCategory,
    excluded_video_ids: set[str] | None = None,
):
    from src.backend.app.services.recommendations import RecommendationCandidate

    excluded_video_ids = excluded_video_ids or set()
    entries = list(
        db.scalars(
            select(VideoCacheEntry).where(
                VideoCacheEntry.workout_category_id == category.id,
                VideoCacheEntry.status.in_(("confirmed_playable", "needs_replacement")),
            )
        ).all()
    )
    entries = [
        entry for entry in entries if entry.youtube_video_id not in excluded_video_ids
    ]
    if not entries:
        return None

    selected = sorted(
        entries,
        key=lambda entry: (
            1 if entry.status == "needs_replacement" else 0,
            entry.play_count,
            entry.last_played_at or datetime.min,
            entry.created_at or datetime.min,
        ),
    )[0]
    return RecommendationCandidate(
        title=selected.title,
        youtube_video_id=selected.youtube_video_id,
        youtube_url=selected.youtube_url,
        duration_seconds=selected.duration_seconds,
        provider="video-cache",
        safety_notes=selected.safety_notes or "Confirmed playable workout video from the deterministic cache.",
        agent_summary=(
            selected.curator_summary
            or "Video Curator selected the least-played confirmed video for this workout category."
        ),
    )


def record_cache_play(db: Session, youtube_video_id: str | None) -> None:
    if not youtube_video_id or youtube_video_id.startswith("mock-"):
        return

    entry = db.scalar(
        select(VideoCacheEntry).where(VideoCacheEntry.youtube_video_id == youtube_video_id)
    )
    if entry is None or entry.status != "confirmed_playable":
        return

    entry.play_count += 1
    entry.last_played_at = datetime.now(UTC).replace(tzinfo=None)
    if entry.play_count >= settings.video_cache_max_play_count:
        entry.status = "needs_replacement"


def confirm_session_video_in_cache(db: Session, video_session: VideoSession) -> None:
    if not video_session.youtube_video_id or video_session.youtube_video_id.startswith("mock-"):
        return
    if video_session.provider not in {"youtube", "youtube-pending", "youtube-cached", "video-cache"}:
        return

    entry = db.scalar(
        select(VideoCacheEntry).where(
            VideoCacheEntry.youtube_video_id == video_session.youtube_video_id
        )
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    if entry is None:
        entry = VideoCacheEntry(
            workout_category_id=video_session.workout_category_id,
            title=video_session.title or "Workout video",
            youtube_video_id=video_session.youtube_video_id,
            youtube_url=video_session.youtube_url
            or f"https://www.youtube.com/watch?v={video_session.youtube_video_id}",
            duration_seconds=video_session.duration_seconds or 600,
            provider="youtube",
            status="confirmed_playable",
            safety_notes=video_session.safety_notes,
            curator_summary=(
                "Frontend playback confirmed this video, so the deterministic curator can reuse it."
            ),
            confirmed_at=now,
        )
        db.add(entry)
        return

    entry.workout_category_id = video_session.workout_category_id
    entry.title = video_session.title or entry.title
    entry.youtube_url = video_session.youtube_url or entry.youtube_url
    entry.duration_seconds = video_session.duration_seconds or entry.duration_seconds
    entry.status = "confirmed_playable"
    entry.safety_notes = video_session.safety_notes or entry.safety_notes
    entry.confirmed_at = entry.confirmed_at or now


def maintain_video_cache(db: Session) -> dict[str, int]:
    categories = list(
        db.scalars(
            select(WorkoutCategory)
            .where(WorkoutCategory.is_active.is_(True))
            .order_by(WorkoutCategory.id)
        ).all()
    )
    created = 0
    for category in categories:
        created += maintain_category_cache(db, category)
    db.commit()
    return {"created_pending": created, "categories": len(categories)}


def maintain_category_cache(db: Session, category: WorkoutCategory) -> int:
    if not settings.youtube_api_key:
        return 0

    confirmed_count = db.scalar(
        select(func.count(VideoCacheEntry.id)).where(
            VideoCacheEntry.workout_category_id == category.id,
            VideoCacheEntry.status == "confirmed_playable",
            VideoCacheEntry.play_count < settings.video_cache_max_play_count,
        )
    )
    if confirmed_count is None:
        confirmed_count = 0

    created = 0
    excluded_video_ids = {
        value
        for value in db.scalars(
            select(VideoCacheEntry.youtube_video_id).where(
                VideoCacheEntry.workout_category_id == category.id
            )
        ).all()
        if value
    }
    while confirmed_count + created < settings.video_cache_target_per_category:
        from src.backend.app.services.recommendations import youtube_recommendation

        candidate = youtube_recommendation(category, excluded_video_ids)
        if candidate is None:
            break
        excluded_video_ids.add(candidate.youtube_video_id)
        if upsert_pending_candidate(db, category, candidate):
            created += 1
        else:
            break
    return created


def upsert_pending_candidate(db: Session, category: WorkoutCategory, candidate) -> bool:
    existing = db.scalar(
        select(VideoCacheEntry).where(
            VideoCacheEntry.youtube_video_id == candidate.youtube_video_id
        )
    )
    if existing is not None:
        return False

    db.add(
        VideoCacheEntry(
            workout_category_id=category.id,
            title=candidate.title,
            youtube_video_id=candidate.youtube_video_id,
            youtube_url=candidate.youtube_url,
            duration_seconds=candidate.duration_seconds,
            provider="youtube",
            status="pending_playback",
            safety_notes=candidate.safety_notes,
            curator_summary=(
                "Deterministic Video Curator found an embeddable YouTube candidate. "
                "It will enter the playable cache after browser playback confirmation."
            ),
        )
    )
    return True


def start_video_curator_scheduler() -> None:
    global _curator_thread
    if not settings.video_curator_enabled or _curator_thread is not None:
        return

    _curator_stop_event.clear()
    _curator_thread = Thread(target=_curator_loop, name="fithub-video-curator", daemon=True)
    _curator_thread.start()


def stop_video_curator_scheduler() -> None:
    global _curator_thread
    _curator_stop_event.set()
    if _curator_thread is not None:
        _curator_thread.join(timeout=1)
        _curator_thread = None


def _curator_loop() -> None:
    interval_seconds = max(1, settings.video_curator_interval_hours) * 3600
    while not _curator_stop_event.wait(interval_seconds):
        with SessionLocal() as db:
            maintain_video_cache(db)
