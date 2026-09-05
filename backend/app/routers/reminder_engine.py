from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

from app.models.training import Training
from app.models.reminder import Reminder

from app.schemas.reminder import ReminderResponse

from app.services.reminder_engine import get_training_reminders


router = APIRouter(
    prefix="/api/reminder-engine",
    tags=["Reminder Engine"],
)


@router.post(
    "/training/{training_id}/generate"
)
async def generate_training_reminders(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------------
    # Find training
    # --------------------------------------------------------

    result = await db.execute(
        select(Training)
        .where(Training.id == training_id)
    )

    training = result.scalar_one_or_none()

    if training is None:
        raise HTTPException(
            status_code=404,
            detail="Training not found.",
        )

    # --------------------------------------------------------
    # Generate reminders
    # --------------------------------------------------------

    reminders = await get_training_reminders(
        training,
        db,
    )

    return {
        "success": True,
        "message": "Training reminders generated successfully.",
        "training_id": training_id,
        "training_name": training.training_name,
        "reminders_created": len(reminders),
    }


@router.get(
    "/training/{training_id}",
    response_model=list[ReminderResponse],
)
async def get_training_reminders_list(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder)
        .where(
            Reminder.training_id == training_id
        )
        .order_by(Reminder.scheduled_at)
    )

    return result.scalars().all()


@router.get(
    "",
    response_model=list[ReminderResponse],
)
async def get_all_reminders(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder)
        .order_by(Reminder.scheduled_at)
    )

    return result.scalars().all()