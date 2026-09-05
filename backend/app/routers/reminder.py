from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

from app.models.reminder_config import ReminderConfig
from app.models.reminder_recipient import ReminderRecipient

from app.schemas.reminder import (
    ReminderConfigCreate,
    ReminderConfigResponse,
    ReminderConfigUpdate,
    ReminderRecipientCreate,
    ReminderRecipientResponse,
)


router = APIRouter(
    prefix="/api/reminders/config",
    tags=["Reminder Configuration"],
)


# ============================================================
# REMINDER CONFIGURATION
# ============================================================

@router.get(
    "",
    response_model=list[ReminderConfigResponse],
)
async def get_reminder_configs(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReminderConfig)
        .order_by(ReminderConfig.id)
    )

    return result.scalars().all()


@router.get(
    "/{config_id}",
    response_model=ReminderConfigResponse,
)
async def get_reminder_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReminderConfig)
        .where(ReminderConfig.id == config_id)
    )

    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder configuration not found.",
        )

    return config


@router.post(
    "",
    response_model=ReminderConfigResponse,
    status_code=201,
)
async def create_reminder_config(
    data: ReminderConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    config = ReminderConfig(
        name=data.name,
        reminder_type=data.reminder_type.value,
        days_before=data.days_before,
        send_time=data.send_time,
        enabled=data.enabled,
    )

    db.add(config)

    await db.commit()
    await db.refresh(config)

    return config


@router.put(
    "/{config_id}",
    response_model=ReminderConfigResponse,
)
async def update_reminder_config(
    config_id: int,
    data: ReminderConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReminderConfig)
        .where(ReminderConfig.id == config_id)
    )

    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder configuration not found.",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "reminder_type" in update_data:
        reminder_type = update_data["reminder_type"]

        if hasattr(reminder_type, "value"):
            update_data["reminder_type"] = reminder_type.value

    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config


@router.delete(
    "/{config_id}"
)
async def delete_reminder_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReminderConfig)
        .where(ReminderConfig.id == config_id)
    )

    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder configuration not found.",
        )

    await db.delete(config)
    await db.commit()

    return {
        "success": True,
        "message": "Reminder configuration deleted successfully.",
    }


# ============================================================
# RECIPIENT MANAGEMENT
# ============================================================

@router.get(
    "/{config_id}/recipients",
)
async def get_recipients(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------------
    # Check reminder configuration
    # --------------------------------------------------------

    result = await db.execute(
        select(ReminderConfig)
        .where(ReminderConfig.id == config_id)
    )

    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder configuration not found.",
        )

    # --------------------------------------------------------
    # Get recipients
    # --------------------------------------------------------

    result = await db.execute(
        select(ReminderRecipient)
        .where(
            ReminderRecipient.reminder_config_id == config_id
        )
        .order_by(ReminderRecipient.id)
    )

    recipients = result.scalars().all()

    return {
        "reminder_config_id": config_id,
        "recipients": [
            {
                "id": recipient.id,
                "reminder_config_id": recipient.reminder_config_id,
                "recipient_type": recipient.recipient_type,
                "recipient_id": recipient.recipient_id,
                "channel": recipient.channel,
            }
            for recipient in recipients
        ],
    }


@router.post(
    "/{config_id}/recipients",
    response_model=ReminderRecipientResponse,
    status_code=201,
)
async def add_recipient(
    config_id: int,
    data: ReminderRecipientCreate,
    db: AsyncSession = Depends(get_db),
):
    # --------------------------------------------------------
    # Check reminder configuration
    # --------------------------------------------------------

    result = await db.execute(
        select(ReminderConfig)
        .where(ReminderConfig.id == config_id)
    )

    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder configuration not found.",
        )

    # --------------------------------------------------------
    # Convert enums to strings
    # --------------------------------------------------------

    recipient_type = data.recipient_type.value
    channel = data.channel.value

    # --------------------------------------------------------
    # Prevent duplicate recipient
    # --------------------------------------------------------

    existing_result = await db.execute(
        select(ReminderRecipient)
        .where(
            ReminderRecipient.reminder_config_id == config_id,
            ReminderRecipient.recipient_type == recipient_type,
            ReminderRecipient.recipient_id == data.recipient_id,
            ReminderRecipient.channel == channel,
        )
    )

    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "This recipient is already configured "
                "for this reminder."
            ),
        )

    # --------------------------------------------------------
    # Create recipient
    # --------------------------------------------------------

    recipient = ReminderRecipient(
        reminder_config_id=config_id,
        recipient_type=recipient_type,
        recipient_id=data.recipient_id,
        channel=channel,
    )

    db.add(recipient)

    await db.commit()
    await db.refresh(recipient)

    return recipient


@router.delete(
    "/{config_id}/recipients/{recipient_id}"
)
async def delete_recipient(
    config_id: int,
    recipient_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReminderRecipient)
        .where(
            ReminderRecipient.id == recipient_id,
            ReminderRecipient.reminder_config_id == config_id,
        )
    )

    recipient = result.scalar_one_or_none()

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found.",
        )

    await db.delete(recipient)
    await db.commit()

    return {
        "success": True,
        "message": "Recipient removed successfully.",
    }