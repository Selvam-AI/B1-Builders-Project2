from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.models import TimeSlot, WorkoutCategory
from src.backend.app.services.auth import seed_admin_user


WORKOUT_CATEGORIES = [
    {
        "name": "Upper Body",
        "slug": "upper-body",
        "description": "General upper body strength and mobility workouts.",
    },
    {
        "name": "Lower Body",
        "slug": "lower-body",
        "description": "General lower body strength and mobility workouts.",
    },
    {
        "name": "Cardio",
        "slug": "cardio",
        "description": "Beginner-friendly cardio and low-impact conditioning workouts.",
    },
]


def format_slot_label(start_hour: int) -> str:
    end_hour = start_hour + 1
    return f"{format_hour(start_hour)} - {format_hour(end_hour)}"


def format_hour(hour: int) -> str:
    suffix = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    return f"{display_hour}:00 {suffix}"


def seed_database(db: Session) -> None:
    seed_time_slots(db)
    seed_workout_categories(db)
    if settings.seed_admin:
        seed_admin_user(db, settings.admin_email, settings.admin_password)
    db.commit()


def seed_time_slots(db: Session) -> None:
    existing_hours = set(db.scalars(select(TimeSlot.start_hour)).all())
    for start_hour in range(9, 21):
        if start_hour in existing_hours:
            continue
        db.add(
            TimeSlot(
                label=format_slot_label(start_hour),
                start_hour=start_hour,
                end_hour=start_hour + 1,
                capacity=20,
                is_active=True,
            )
        )
    if -1 not in existing_hours:
        db.add(
            TimeSlot(
                label="Demo time slot",
                start_hour=-1,
                end_hour=-1,
                capacity=20,
                is_active=True,
                is_demo=True,
            )
        )


def seed_workout_categories(db: Session) -> None:
    existing_slugs = set(db.scalars(select(WorkoutCategory.slug)).all())
    for category in WORKOUT_CATEGORIES:
        if category["slug"] in existing_slugs:
            continue
        db.add(WorkoutCategory(**category, is_active=True))
