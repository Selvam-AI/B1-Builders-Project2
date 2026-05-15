from dataclasses import dataclass
import logging
import re

from fastapi import HTTPException, status
from googleapiclient.discovery import build
from litellm import completion
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.models import TimeSlot, VideoSession, WorkoutCategory
from src.backend.app.services.video_curator import (
    confirm_session_video_in_cache,
    select_cached_candidate,
)

logger = logging.getLogger("fithub.recommendations")


def debug_print(message: str) -> None:
    if not settings.debug:
        return
    print(f"[FitHub AI] {message}", flush=True)


@dataclass(frozen=True)
class RecommendationCandidate:
    title: str
    youtube_video_id: str
    youtube_url: str
    duration_seconds: int
    provider: str
    safety_notes: str
    agent_summary: str


MOCK_CANDIDATES = {
    "upper-body": RecommendationCandidate(
        title="10 Minute Beginner Upper Body Workout",
        youtube_video_id="HRvFxrFGqA4",
        youtube_url="https://www.youtube.com/watch?v=HRvFxrFGqA4",
        duration_seconds=600,
        provider="mock",
        safety_notes="Low-impact upper-body routine suitable for a general prototype audience.",
        agent_summary=(
            "Deterministic curator selected an upper-body beginner workout because the routine is "
            "short, simple, and not high intensity."
        ),
    ),
    "lower-body": RecommendationCandidate(
        title="10 Minute Beginner Lower Body Workout",
        youtube_video_id="YyBcMVQylas",
        youtube_url="https://www.youtube.com/watch?v=YyBcMVQylas",
        duration_seconds=600,
        provider="mock",
        safety_notes="Low-impact lower-body routine suitable for a general prototype audience.",
        agent_summary=(
            "Deterministic curator selected a lower-body beginner workout because the routine is "
            "short, simple, and not high intensity."
        ),
    ),
    "cardio": RecommendationCandidate(
        title="10 Minute Beginner Cardio Workout",
        youtube_video_id="VWj8ZxCxrYk",
        youtube_url="https://www.youtube.com/watch?v=VWj8ZxCxrYk",
        duration_seconds=600,
        provider="mock",
        safety_notes="Beginner-friendly cardio routine suitable for a general prototype audience.",
        agent_summary=(
            "Deterministic curator selected a beginner cardio workout because the routine is "
            "short, simple, and suitable for low-impact conditioning."
        ),
    ),
}


def get_or_create_video_recommendation(
    db: Session,
    time_slot_id: int,
    workout_category_id: int,
) -> VideoSession:
    logger.info(
        "Recommendation request: time_slot_id=%s workout_category_id=%s provider=%s mode=%s youtube_key_present=%s",
        time_slot_id,
        workout_category_id,
        settings.ai_llm_provider,
        settings.ai_recommender_mode,
        bool(settings.youtube_api_key),
    )
    debug_print(
        "Recommendation request "
        f"time_slot_id={time_slot_id} workout_category_id={workout_category_id} "
        f"llm_provider={settings.ai_llm_provider} recommender_mode={settings.ai_recommender_mode} "
        f"youtube_key_present={bool(settings.youtube_api_key)}"
    )
    time_slot = db.get(TimeSlot, time_slot_id)
    if time_slot is None or not time_slot.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot is not available.",
        )

    category = db.get(WorkoutCategory, workout_category_id)
    if category is None or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout category is not available.",
        )

    existing = db.scalar(
        select(VideoSession).where(
            VideoSession.time_slot_id == time_slot.id,
            VideoSession.workout_category_id == category.id,
        )
    )
    if existing is not None:
        logger.info(
            "Recommendation cache hit: video_session_id=%s provider=%s video_id=%s status=%s",
            existing.id,
            existing.provider,
            existing.youtube_video_id,
            existing.status,
        )
        debug_print(
            "Recommendation cache hit "
            f"video_session_id={existing.id} provider={existing.provider} "
            f"video_id={existing.youtube_video_id} status={existing.status}"
        )
        if should_refresh_existing_video(existing):
            logger.info("Recommendation will attempt fresh YouTube search before cached fallback.")
            debug_print("Recommendation will attempt fresh YouTube search before cached fallback.")
            candidate = select_recommendation_candidate(db, category)
            update_video_session(existing, mark_fresh_youtube_pending(candidate))
            db.commit()
            db.refresh(existing)
        return existing

    candidate = mark_fresh_youtube_pending(select_recommendation_candidate(db, category))
    logger.info(
        "Recommendation selected: provider=%s video_id=%s title=%s",
        candidate.provider,
        candidate.youtube_video_id,
        candidate.title,
    )
    debug_print(
        "Recommendation selected "
        f"provider={candidate.provider} video_id={candidate.youtube_video_id} title={candidate.title}"
    )
    session = VideoSession(
        time_slot_id=time_slot.id,
        workout_category_id=category.id,
        title=candidate.title,
        youtube_video_id=candidate.youtube_video_id,
        youtube_url=candidate.youtube_url,
        duration_seconds=candidate.duration_seconds,
        provider=candidate.provider,
        status="approved",
        safety_notes=candidate.safety_notes,
        agent_summary=candidate.agent_summary,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def select_recommendation_candidate(
    db: Session,
    category: WorkoutCategory,
    excluded_video_ids: set[str] | None = None,
) -> RecommendationCandidate:
    excluded_video_ids = excluded_video_ids or set()
    cached_candidate = select_cached_candidate(db, category, excluded_video_ids)
    if cached_candidate is not None:
        debug_print(
            "Confirmed video-cache candidate selected "
            f"video_id={cached_candidate.youtube_video_id}"
        )
        return cached_candidate

    if should_use_mock_recommendation():
        logger.info(
            "Mock recommendation selected before YouTube search: mode=%s youtube_key_present=%s fallback=%s",
            settings.ai_recommender_mode,
            bool(settings.youtube_api_key),
            settings.ai_allow_mock_fallback,
        )
        debug_print(
            "Mock recommendation selected before YouTube search "
            f"mode={settings.ai_recommender_mode} youtube_key_present={bool(settings.youtube_api_key)} "
            f"fallback={settings.ai_allow_mock_fallback}"
        )
        cached_candidate = cached_embeddable_recommendation(db, category, excluded_video_ids)
        if cached_candidate is not None:
            debug_print(
                "Cached embeddable video selected because recommender is in mock/no-key mode "
                f"video_id={cached_candidate.youtube_video_id}"
            )
            return cached_candidate
        return mock_recommendation(category)

    candidate = youtube_recommendation(category, excluded_video_ids)
    if candidate is None:
        logger.info("YouTube embeddable search did not return a usable candidate; checking cached videos.")
        debug_print("YouTube embeddable search did not return a usable candidate; checking cached videos.")
        candidate = cached_embeddable_recommendation(db, category, excluded_video_ids)
        if candidate is None:
            logger.info("No cached embeddable video found; using mock fallback.")
            debug_print("No cached embeddable video found; using mock fallback.")
            candidate = mock_recommendation(category)
        else:
            logger.info(
                "Cached embeddable fallback selected: video_id=%s title=%s",
                candidate.youtube_video_id,
                candidate.title,
            )
            debug_print(
                "Cached embeddable fallback selected "
                f"video_id={candidate.youtube_video_id} title={candidate.title}"
            )

    reviewed_candidate = llm_review_candidate(category, candidate)
    if reviewed_candidate is not None:
        logger.info(
            "LiteLLM review completed with provider=%s for video_id=%s",
            settings.ai_llm_provider,
            reviewed_candidate.youtube_video_id,
        )
        debug_print(
            "LiteLLM review completed "
            f"provider={settings.ai_llm_provider} video_id={reviewed_candidate.youtube_video_id}"
        )
        return reviewed_candidate

    if settings.ai_allow_mock_fallback:
        return candidate

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="AI recommendation provider is not available and mock fallback is disabled.",
    )


def should_use_mock_recommendation() -> bool:
    if settings.ai_recommender_mode.lower() == "mock":
        return True
    if not settings.youtube_api_key:
        return settings.ai_allow_mock_fallback
    return False


def should_refresh_existing_video(video_session: VideoSession) -> bool:
    if settings.ai_recommender_mode.lower() == "mock":
        return False
    return True


def update_video_session(video_session: VideoSession, candidate: RecommendationCandidate) -> None:
    video_session.title = candidate.title
    video_session.youtube_video_id = candidate.youtube_video_id
    video_session.youtube_url = candidate.youtube_url
    video_session.duration_seconds = candidate.duration_seconds
    video_session.provider = candidate.provider
    video_session.status = "approved"
    video_session.safety_notes = candidate.safety_notes
    video_session.agent_summary = candidate.agent_summary


def replace_failed_video_recommendation(
    db: Session,
    video_session: VideoSession,
    failed_video_id: str | None = None,
    reason: str | None = None,
) -> VideoSession:
    category = db.get(WorkoutCategory, video_session.workout_category_id)
    if category is None or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout category is not available.",
        )

    excluded_video_ids = {
        value
        for value in (video_session.youtube_video_id, failed_video_id)
        if value and not value.startswith("mock-")
    }
    debug_print(
        "Playback failure reported "
        f"video_session_id={video_session.id} failed_video_id={failed_video_id} reason={reason or 'unspecified'}"
    )
    candidate = select_recommendation_candidate(db, category, excluded_video_ids)
    if candidate.youtube_video_id in excluded_video_ids:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No alternate playable video is available right now.",
        )

    update_video_session(video_session, mark_fresh_youtube_pending(candidate))
    db.commit()
    db.refresh(video_session)
    debug_print(
        "Replacement recommendation selected "
        f"video_session_id={video_session.id} provider={video_session.provider} "
        f"video_id={video_session.youtube_video_id}"
    )
    return video_session


def confirm_video_playback(
    db: Session,
    video_session: VideoSession,
    youtube_video_id: str | None = None,
) -> VideoSession:
    if youtube_video_id and video_session.youtube_video_id != youtube_video_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Playback confirmation does not match the active video.",
        )

    if video_session.provider == "youtube-pending":
        video_session.provider = "youtube"
    video_session.status = "approved"
    confirm_session_video_in_cache(db, video_session)
    db.commit()
    db.refresh(video_session)
    debug_print(
        "Playback confirmed "
        f"video_session_id={video_session.id} provider={video_session.provider} "
        f"video_id={video_session.youtube_video_id}"
    )
    return video_session


def mark_fresh_youtube_pending(candidate: RecommendationCandidate) -> RecommendationCandidate:
    if candidate.provider != "youtube":
        return candidate
    return RecommendationCandidate(
        title=candidate.title,
        youtube_video_id=candidate.youtube_video_id,
        youtube_url=candidate.youtube_url,
        duration_seconds=candidate.duration_seconds,
        provider="youtube-pending",
        safety_notes=candidate.safety_notes,
        agent_summary=(
            f"{candidate.agent_summary} Playback must be confirmed in the browser before this video "
            "is reused as a cached fallback."
        )[:500],
    )


def cached_embeddable_recommendation(
    db: Session,
    category: WorkoutCategory,
    excluded_video_ids: set[str] | None = None,
) -> RecommendationCandidate | None:
    excluded_video_ids = excluded_video_ids or set()
    query = select(VideoSession).where(
        VideoSession.workout_category_id == category.id,
        VideoSession.provider.in_(("youtube", "youtube-cached")),
        VideoSession.status == "approved",
        VideoSession.youtube_video_id.is_not(None),
    )
    if excluded_video_ids:
        query = query.where(VideoSession.youtube_video_id.not_in(excluded_video_ids))

    cached = db.scalars(query.order_by(VideoSession.created_at.desc())).first()
    if cached is None:
        return None

    return RecommendationCandidate(
        title=cached.title or f"Cached {category.name} Workout",
        youtube_video_id=str(cached.youtube_video_id),
        youtube_url=cached.youtube_url or f"https://www.youtube.com/watch?v={cached.youtube_video_id}",
        duration_seconds=cached.duration_seconds or 600,
        provider="youtube-cached",
        safety_notes=(
            cached.safety_notes
            or "Previously selected public embeddable YouTube workout reused as a cache fallback."
        ),
        agent_summary=(
            "Fresh YouTube search did not return a usable embeddable video, so the recommender reused "
            "a previously approved embeddable video for this workout category."
        ),
    )


def youtube_recommendation(
    category: WorkoutCategory,
    excluded_video_ids: set[str] | None = None,
) -> RecommendationCandidate | None:
    excluded_video_ids = excluded_video_ids or set()
    if not settings.youtube_api_key:
        logger.info("YouTube search skipped: YOUTUBE_API_KEY is missing.")
        debug_print("YouTube search skipped: YOUTUBE_API_KEY is missing.")
        return None

    try:
        logger.info(
            "YouTube search starting with videoEmbeddable=true for category=%s",
            category.slug,
        )
        debug_print(f"YouTube search starting with videoEmbeddable=true category={category.slug}")
        youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
        search_response = (
            youtube.search()
            .list(
                part="id",
                q=f"10 minute beginner {category.name} workout no equipment",
                type="video",
                videoEmbeddable="true",
                videoDuration="medium",
                safeSearch="strict",
                maxResults=5,
            )
            .execute()
        )
        video_ids = [
            item["id"]["videoId"]
            for item in search_response.get("items", [])
            if item.get("id", {}).get("videoId")
            and item["id"]["videoId"] not in excluded_video_ids
        ]
        if not video_ids:
            logger.info("YouTube search returned no candidate video IDs.")
            debug_print("YouTube search returned no candidate video IDs.")
            return None

        details_response = (
            youtube.videos()
            .list(
                part="snippet,contentDetails,status",
                id=",".join(video_ids),
                maxResults=5,
            )
            .execute()
        )
    except Exception:
        logger.exception("YouTube embeddable search failed; falling back when allowed.")
        debug_print("YouTube embeddable search failed; falling back when allowed.")
        return None

    candidates: list[tuple[int, RecommendationCandidate]] = []
    for item in details_response.get("items", []):
        status_data = item.get("status", {})
        if not status_data.get("embeddable", False) or status_data.get("privacyStatus") != "public":
            logger.info(
                "YouTube candidate rejected: video_id=%s embeddable=%s privacy=%s",
                item.get("id"),
                status_data.get("embeddable"),
                status_data.get("privacyStatus"),
            )
            debug_print(
                "YouTube candidate rejected "
                f"video_id={item.get('id')} embeddable={status_data.get('embeddable')} "
                f"privacy={status_data.get('privacyStatus')}"
            )
            continue

        video_id = item["id"]
        if video_id in excluded_video_ids:
            continue
        snippet = item.get("snippet", {})
        duration_seconds = parse_iso8601_duration(
            item.get("contentDetails", {}).get("duration", "PT10M")
        )
        distance_from_ten_minutes = abs(duration_seconds - 600)
        candidates.append(
            (
                distance_from_ten_minutes,
                RecommendationCandidate(
                    title=snippet.get("title", f"10 Minute {category.name} Workout"),
                    youtube_video_id=video_id,
                    youtube_url=f"https://www.youtube.com/watch?v={video_id}",
                    duration_seconds=duration_seconds,
                    provider="youtube",
                    safety_notes=(
                        "YouTube result was filtered for embeddable, public, beginner-style "
                        "workout content before prototype safety review."
                    ),
                    agent_summary=(
                        f"Deterministic curator selected an embeddable {category.name} workout "
                        "candidate for prototype use."
                    ),
                ),
            )
        )

    if not candidates:
        logger.info("YouTube details returned no public embeddable candidates.")
        debug_print("YouTube details returned no public embeddable candidates.")
        return None

    selected = sorted(candidates, key=lambda item: item[0])[0][1]
    logger.info(
        "YouTube embeddable video selected: video_id=%s title=%s duration=%s",
        selected.youtube_video_id,
        selected.title,
        selected.duration_seconds,
    )
    debug_print(
        "YouTube embeddable video selected "
        f"video_id={selected.youtube_video_id} title={selected.title} duration={selected.duration_seconds}"
    )
    return selected


def parse_iso8601_duration(value: str) -> int:
    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?",
        value,
    )
    if not match:
        return 600

    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def llm_review_candidate(
    category: WorkoutCategory,
    candidate: RecommendationCandidate,
) -> RecommendationCandidate | None:
    try:
        logger.info(
            "LiteLLM review starting: provider=%s model=%s base_url=%s video_id=%s",
            settings.ai_llm_provider,
            settings.model,
            settings.base_url if settings.ai_llm_provider == "ollama" else "default",
            candidate.youtube_video_id,
        )
        debug_print(
            "LiteLLM review starting "
            f"provider={settings.ai_llm_provider} model={settings.model} "
            f"video_id={candidate.youtube_video_id}"
        )
        response = completion(
            model=settings.model,
            api_base=settings.base_url if settings.ai_llm_provider == "ollama" else None,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise fitness safety reviewer. "
                        "Approve only beginner-friendly 10 minute workouts."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Review this {category.name} workout candidate for a general audience: "
                        f"{candidate.title}. Return one short approval sentence."
                    ),
                },
            ],
            timeout=8,
        )
    except Exception:
        logger.exception("LiteLLM review failed; keeping selected candidate when fallback is allowed.")
        debug_print("LiteLLM review failed; keeping selected candidate when fallback is allowed.")
        return None

    message = response.choices[0].message.content if response.choices else ""
    summary = str(message or candidate.agent_summary).strip()
    return RecommendationCandidate(
        title=candidate.title,
        youtube_video_id=candidate.youtube_video_id,
        youtube_url=candidate.youtube_url,
        duration_seconds=candidate.duration_seconds,
        provider=candidate.provider,
        safety_notes=candidate.safety_notes,
        agent_summary=summary[:500],
    )


def mock_recommendation(category: WorkoutCategory) -> RecommendationCandidate:
    if category.slug in MOCK_CANDIDATES:
        return MOCK_CANDIDATES[category.slug]

    return RecommendationCandidate(
        title=f"10 Minute Beginner {category.name} Workout",
        youtube_video_id=f"mock-{category.slug}-10",
        youtube_url=f"https://www.youtube.com/watch?v=mock-{category.slug}-10",
        duration_seconds=600,
        provider="mock",
        safety_notes="Beginner-friendly routine selected by the mock fallback.",
        agent_summary=(
            f"Deterministic curator selected a {category.name} workout through mock fallback "
            "for prototype use."
        ),
    )
