from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.app.models import SlotSignup, TimeSlot, User, WorkoutCategory
from src.backend.app.schemas import OccupancyRead, ReservationCreate


def create_reservation(db: Session, user: User, payload: ReservationCreate) -> SlotSignup:
    time_slot = db.get(TimeSlot, payload.time_slot_id)
    if time_slot is None or not time_slot.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot is not available.",
        )

    category = db.get(WorkoutCategory, payload.workout_category_id)
    if category is None or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout category is not available.",
        )

    existing = db.scalar(
        select(SlotSignup).where(
            SlotSignup.user_id == user.id,
            SlotSignup.time_slot_id == time_slot.id,
        )
    )
    if existing is not None:
        if existing.workout_category_id != category.id:
            existing.workout_category_id = category.id
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member already reserved this time slot.",
        )

    occupancy = count_slot_signups(db, time_slot.id)
    if occupancy >= time_slot.capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is full.",
        )

    signup = SlotSignup(
        user_id=user.id,
        time_slot_id=time_slot.id,
        workout_category_id=category.id,
    )
    db.add(signup)
    db.commit()
    db.refresh(signup)
    return signup


def cancel_reservation(db: Session, user: User, reservation_id: int) -> None:
    signup = db.get(SlotSignup, reservation_id)
    if signup is None or signup.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation was not found for this member.",
        )

    db.delete(signup)
    db.commit()


def list_member_reservations(db: Session, user: User) -> list[SlotSignup]:
    return list(
        db.scalars(
            select(SlotSignup)
            .where(SlotSignup.user_id == user.id)
            .order_by(SlotSignup.created_at.desc(), SlotSignup.id.desc())
        ).all()
    )


def list_slot_occupancy(db: Session) -> list[OccupancyRead]:
    counts = dict(
        db.execute(
            select(SlotSignup.time_slot_id, func.count(SlotSignup.id)).group_by(
                SlotSignup.time_slot_id
            )
        ).all()
    )
    slots = db.scalars(select(TimeSlot).order_by(TimeSlot.start_hour)).all()
    return [
        OccupancyRead(
            time_slot_id=slot.id,
            label=slot.label,
            start_hour=slot.start_hour,
            end_hour=slot.end_hour,
            capacity=slot.capacity,
            current_occupancy=counts.get(slot.id, 0),
            remaining_capacity=max(slot.capacity - counts.get(slot.id, 0), 0),
            is_full=counts.get(slot.id, 0) >= slot.capacity,
            is_demo=slot.is_demo,
        )
        for slot in slots
    ]


def count_slot_signups(db: Session, time_slot_id: int) -> int:
    return (
        db.scalar(
            select(func.count(SlotSignup.id)).where(SlotSignup.time_slot_id == time_slot_id)
        )
        or 0
    )
