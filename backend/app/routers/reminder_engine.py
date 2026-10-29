
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.training import Training
from app.models.reminder import Reminder
from app.models.hod import HOD
from app.models.line_manager import LineManager
from app.schemas.reminder import ReminderResponse
from app.services.reminder_engine import get_training_reminders


router = APIRouter(
    prefix="/api/reminder-engine",
    tags=["Reminder Engine"],
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class ManualReminderRecipient(BaseModel):
    recipient_type: str
    recipient_id: int = Field(gt=0)


class ManualReminderCreate(BaseModel):
    category: str = "TRAINING"
    training_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    scheduled_date: date
    scheduled_time: time = time(9, 0)
    recipient_type: str = "BOTH"
    recipients: list[ManualReminderRecipient] = Field(min_length=1)
    channel: str = "EMAIL"
    custom_message: str = Field(default="", max_length=5000)


# ============================================================
# GENERATE AUTOMATIC TRAINING REMINDERS
# ============================================================

@router.post("/training/{training_id}/generate")
async def generate_training_reminders(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Training).where(Training.id == training_id)
    )
    training = result.scalar_one_or_none()

    if training is None:
        raise HTTPException(
            status_code=404,
            detail="Training not found.",
        )

    reminders = await get_training_reminders(training, db)

    return {
        "success": True,
        "message": "Training reminders generated successfully.",
        "training_id": training_id,
        "training_name": training.training_name,
        "reminders_created": len(reminders),
    }


# ============================================================
# CREATE MANUAL TRAINING REMINDERS
# ============================================================

@router.post("/manual")
async def create_manual_training_reminder(
    payload: ManualReminderCreate,
    db: AsyncSession = Depends(get_db),
):
    if payload.category.strip().upper() != "TRAINING":
        raise HTTPException(
            status_code=400,
            detail="Reminder category must be TRAINING.",
        )

    if payload.channel.strip().upper() != "EMAIL":
        raise HTTPException(
            status_code=400,
            detail="Manual reminders currently support EMAIL only.",
        )

    recipient_type = payload.recipient_type.strip().upper()

    if recipient_type not in {"BOTH", "HOD", "LINE_MANAGER"}:
        raise HTTPException(
            status_code=400,
            detail="Recipient type must be BOTH, HOD, or LINE_MANAGER.",
        )

    title = payload.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Reminder title is required.",
        )

    scheduled_at = datetime.combine(
        payload.scheduled_date,
        payload.scheduled_time,
    )

    # This project currently uses naive local datetimes.
    # Keep the API and Celery worker timezone consistent.
    if scheduled_at <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Scheduled date and time must be in the future.",
        )

    training_result = await db.execute(
        select(Training).where(Training.id == payload.training_id)
    )
    training = training_result.scalar_one_or_none()

    if training is None:
        raise HTTPException(
            status_code=404,
            detail="Selected training was not found.",
        )

    # Deduplicate repeated selections.
    unique_recipients = {}

    for item in payload.recipients:
        kind = item.recipient_type.strip().upper()

        if kind not in {"HOD", "LINE_MANAGER"}:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid recipient type: {kind}.",
            )

        if recipient_type != "BOTH" and kind != recipient_type:
            raise HTTPException(
                status_code=400,
                detail="Selected recipients do not match recipient type.",
            )

        unique_recipients[(kind, item.recipient_id)] = item

    if not unique_recipients:
        raise HTTPException(
            status_code=400,
            detail="Select at least one recipient.",
        )

    created = []

    try:
        for kind, person_id in unique_recipients:
            model = HOD if kind == "HOD" else LineManager

            person_result = await db.execute(
                select(model).where(model.id == person_id)
            )
            person = person_result.scalar_one_or_none()

            if person is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{kind} recipient ID {person_id} was not found.",
                )

            email = (getattr(person, "email", None) or "").strip()

            # Basic server-side validation. The actual send provider
            # remains responsible for final address acceptance.
            if (
                not email
                or "@" not in email
                or email.startswith("@")
                or email.endswith("@")
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"{kind} recipient ID {person_id} "
                        "does not have a valid email address."
                    ),
                )

            reminder = Reminder(
                training_id=training.id,
                reminder_type="MANUAL_TRAINING",
                title=title,
                custom_message=payload.custom_message.strip() or None,
                recipient_type=kind,
                recipient_id=person_id,
                channel="EMAIL",
                scheduled_at=scheduled_at,
                status="PENDING",
            )

            db.add(reminder)
            created.append(reminder)

        await db.flush()

        reminder_ids = [reminder.id for reminder in created]

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return {
        "success": True,
        "message": (
            f"Manual reminder scheduled for {len(created)} recipient(s)."
        ),
        "category": "TRAINING",
        "training_id": training.id,
        "training_name": training.training_name,
        "title": title,
        "scheduled_at": scheduled_at,
        "recipient_type": recipient_type,
        "channel": "EMAIL",
        "reminders_created": len(created),
        "reminder_ids": reminder_ids,
    }


# ============================================================
# GET REMINDERS FOR ONE TRAINING
# ============================================================

@router.get(
    "/training/{training_id}",
    response_model=list[ReminderResponse],
)
async def get_training_reminders_list(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    training_result = await db.execute(
        select(Training).where(Training.id == training_id)
    )

    if training_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Training not found.",
        )

    result = await db.execute(
        select(Reminder)
        .where(Reminder.training_id == training_id)
        .order_by(Reminder.scheduled_at)
    )

    return result.scalars().all()


# ============================================================
# GET ALL REMINDERS - ENRICHED HISTORY
# ============================================================

@router.get("")
async def get_all_reminders(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder).order_by(Reminder.scheduled_at.desc())
    )

    reminders = result.scalars().all()
    response = []

    for reminder in reminders:
        # Training details
        training_result = await db.execute(
            select(Training).where(
                Training.id == reminder.training_id
            )
        )
        training = training_result.scalar_one_or_none()

        # Master-data recipient details
        recipient_name = None
        recipient_email = None
        recipient_whatsapp = None

        if reminder.recipient_type == "HOD":
            recipient_result = await db.execute(
                select(HOD).where(HOD.id == reminder.recipient_id)
            )
            recipient = recipient_result.scalar_one_or_none()

            if recipient:
                recipient_name = recipient.name
                recipient_email = recipient.email
                recipient_whatsapp = recipient.whatsapp_number

        elif reminder.recipient_type == "LINE_MANAGER":
            recipient_result = await db.execute(
                select(LineManager).where(
                    LineManager.id == reminder.recipient_id
                )
            )
            recipient = recipient_result.scalar_one_or_none()

            if recipient:
                recipient_name = recipient.name
                recipient_email = recipient.email
                recipient_whatsapp = recipient.whatsapp_number

        response.append(
            {
                "id": reminder.id,
                "training_id": reminder.training_id,
                "training_name": (
                    training.training_name if training else None
                ),
                "training_date": (
                    training.scheduled_date if training else None
                ),
                "training_time": (
                    training.scheduled_time if training else None
                ),
                "trainer_name": (
                    training.trainer_name if training else None
                ),
                "title": reminder.title,
                "custom_message": reminder.custom_message,
                "reminder_type": reminder.reminder_type,
                "recipient_type": reminder.recipient_type,
                "recipient_id": reminder.recipient_id,
                "recipient_name": recipient_name,
                "recipient_email": recipient_email,
                "recipient_whatsapp": recipient_whatsapp,
                "channel": reminder.channel,
                "scheduled_at": reminder.scheduled_at,
                "status": reminder.status,
                "sent_at": reminder.sent_at,
                "failure_reason": reminder.failure_reason,
                "whatsapp_message_id": reminder.whatsapp_message_id,
                "created_at": reminder.created_at,
            }
        )

    return response
