from datetime import datetime, date, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import Training
from app.models.reminder_config import ReminderConfig
from app.models.reminder_recipient import ReminderRecipient
from app.models.reminder import Reminder


async def get_training_reminders(
    training: Training,
    db: AsyncSession,
):
    """
    Calculate which reminders should be created for a training.
    """

    result = await db.execute(
        select(ReminderConfig)
        .where(ReminderConfig.enabled == True)
        .order_by(ReminderConfig.id)
    )

    configs = result.scalars().all()

    reminders_to_create = []

    for config in configs:

        reminder_date = None

        # --------------------------------------------------
        # MONTHLY
        # --------------------------------------------------

        if config.reminder_type == "MONTHLY":

            # Monthly reminder is generated on the
            # first day of the training month.
            reminder_date = training.scheduled_date.replace(day=1)

        # --------------------------------------------------
        # WEEKLY
        # --------------------------------------------------

        elif config.reminder_type == "WEEKLY":

            # Monday of the training week
            reminder_date = (
                training.scheduled_date
                - timedelta(
                    days=training.scheduled_date.weekday()
                )
            )

        # --------------------------------------------------
        # BEFORE TRAINING
        # --------------------------------------------------

        elif config.reminder_type == "BEFORE_TRAINING":

            if config.days_before is None:
                continue

            reminder_date = (
                training.scheduled_date
                - timedelta(
                    days=config.days_before
                )
            )

        # --------------------------------------------------
        # POST TRAINING
        # --------------------------------------------------

        elif config.reminder_type == "POST_TRAINING":

            reminder_date = training.scheduled_date

        # --------------------------------------------------
        # DOCUMENT SUBMISSION
        # --------------------------------------------------

        elif config.reminder_type == "DOCUMENT_SUBMISSION":

            reminder_date = training.scheduled_date + timedelta(days=1)

        # --------------------------------------------------
        # TRAINING PERCENTAGE
        # --------------------------------------------------

        elif config.reminder_type == "TRAINING_PERCENTAGE":

            # First day of following month
            if training.scheduled_date.month == 12:
                reminder_date = date(
                    training.scheduled_date.year + 1,
                    1,
                    1,
                )
            else:
                reminder_date = date(
                    training.scheduled_date.year,
                    training.scheduled_date.month + 1,
                    1,
                )

        else:
            continue

        # --------------------------------------------------
        # SEND TIME
        # --------------------------------------------------

        send_time = config.send_time or time(
            hour=9,
            minute=0,
        )

        scheduled_at = datetime.combine(
            reminder_date,
            send_time,
        )

        # --------------------------------------------------
        # GET RECIPIENTS
        # --------------------------------------------------

        recipient_result = await db.execute(
            select(ReminderRecipient)
            .where(
                ReminderRecipient.reminder_config_id
                == config.id
            )
        )

        recipients = recipient_result.scalars().all()

        for recipient in recipients:

            # ------------------------------------------------
            # Avoid duplicate reminder
            # ------------------------------------------------

            existing_result = await db.execute(
                select(Reminder)
                .where(
                    Reminder.training_id == training.id,
                    Reminder.reminder_type
                    == config.reminder_type,
                    Reminder.recipient_type
                    == recipient.recipient_type,
                    Reminder.recipient_id
                    == recipient.recipient_id,
                    Reminder.channel
                    == recipient.channel,
                    Reminder.scheduled_at
                    == scheduled_at,
                )
            )

            existing = existing_result.scalar_one_or_none()

            if existing:
                continue

            reminder = Reminder(
                training_id=training.id,
                reminder_type=config.reminder_type,
                recipient_type=recipient.recipient_type,
                recipient_id=recipient.recipient_id,
                channel=recipient.channel,
                scheduled_at=scheduled_at,
                status="PENDING",
            )

            db.add(reminder)

            reminders_to_create.append(reminder)

    await db.commit()

    return reminders_to_create