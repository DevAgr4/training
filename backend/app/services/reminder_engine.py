from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import Training
from app.models.reminder import Reminder
from app.models.hod import HOD
from app.models.line_manager import LineManager
from app.models.training_document import TrainingDocument


# ============================================================
# DEFAULTS
# ============================================================

DEFAULT_SEND_TIME = time(
    hour=9,
    minute=0,
)


# ============================================================
# PRE-TRAINING REMINDER RULES
# ============================================================

PRE_TRAINING_RULES = [
    (
        "BEFORE_TRAINING_7_DAYS",
        7,
    ),
    (
        "BEFORE_TRAINING_2_DAYS",
        2,
    ),
    (
        "BEFORE_TRAINING_1_DAY",
        1,
    ),
]


# ============================================================
# POST-TRAINING REMINDER RULES
# ============================================================

POST_TRAINING_RULES = [
    (
        "IMMEDIATE",
        0,
    ),
    (
        "2_DAYS",
        2,
    ),
    (
        "7_DAYS",
        7,
    ),
]


# ============================================================
# GET TARGET-AUDIENCE RECIPIENTS
# ============================================================

async def get_active_reminder_recipients(
    training: Training,
    db: AsyncSession,
):
    """
    Resolve HOD and Line Manager recipients through the
    Training.audience_id -> recipient.audience_id relationship.

    The Settings master data owns the recipient information.

    For a training:

        Training.audience_id
                 |
                 +---- HOD.audience_id
                 |
                 +---- LineManager.audience_id

    A recipient can receive:
        EMAIL    when an email address exists
        WHATSAPP when a WhatsApp number exists

    Returns dictionaries containing:
        recipient_type
        recipient_id
        channel
    """

    audience_id = getattr(
        training,
        "audience_id",
        None,
    )

    if audience_id is None:
        return []

    recipients = []
    seen = set()

    # --------------------------------------------------------
    # HODs
    # --------------------------------------------------------

    hod_result = await db.execute(
        select(HOD).where(
            HOD.audience_id == audience_id
        )
    )

    hods = hod_result.scalars().all()

    for hod in hods:

        if hod.email:
            key = (
                "HOD",
                hod.id,
                "EMAIL",
            )

            if key not in seen:
                seen.add(key)

                recipients.append(
                    {
                        "recipient_type": "HOD",
                        "recipient_id": hod.id,
                        "channel": "EMAIL",
                    }
                )

        if hod.whatsapp_number:
            key = (
                "HOD",
                hod.id,
                "WHATSAPP",
            )

            if key not in seen:
                seen.add(key)

                recipients.append(
                    {
                        "recipient_type": "HOD",
                        "recipient_id": hod.id,
                        "channel": "WHATSAPP",
                    }
                )

    # --------------------------------------------------------
    # Line Managers
    # --------------------------------------------------------

    manager_result = await db.execute(
        select(LineManager).where(
            LineManager.audience_id == audience_id
        )
    )

    managers = manager_result.scalars().all()

    for manager in managers:

        if manager.email:
            key = (
                "LINE_MANAGER",
                manager.id,
                "EMAIL",
            )

            if key not in seen:
                seen.add(key)

                recipients.append(
                    {
                        "recipient_type": "LINE_MANAGER",
                        "recipient_id": manager.id,
                        "channel": "EMAIL",
                    }
                )

        if manager.whatsapp_number:
            key = (
                "LINE_MANAGER",
                manager.id,
                "WHATSAPP",
            )

            if key not in seen:
                seen.add(key)

                recipients.append(
                    {
                        "recipient_type": "LINE_MANAGER",
                        "recipient_id": manager.id,
                        "channel": "WHATSAPP",
                    }
                )

    return recipients


# ============================================================
# CHECK REMINDER DUPLICATE
# ============================================================

async def reminder_exists(
    training_id: int,
    reminder_type: str,
    recipient_type: str,
    recipient_id: int,
    channel: str,
    scheduled_at: datetime,
    db: AsyncSession,
):
    result = await db.execute(
        select(Reminder).where(
            Reminder.training_id == training_id,

            Reminder.reminder_type
            == reminder_type,

            Reminder.recipient_type
            == recipient_type,

            Reminder.recipient_id
            == recipient_id,

            Reminder.channel
            == channel,

            Reminder.scheduled_at
            == scheduled_at,
        )
    )

    return result.scalar_one_or_none()


# ============================================================
# CREATE REMINDER
# ============================================================

async def create_reminder(
    training_id: int,
    reminder_type: str,
    recipient,
    scheduled_at: datetime,
    db: AsyncSession,
):
    """
    Create a reminder only if the same reminder does not
    already exist.

    recipient is a dictionary created by
    get_active_reminder_recipients().
    """

    recipient_type = recipient[
        "recipient_type"
    ]

    recipient_id = recipient[
        "recipient_id"
    ]

    channel = recipient[
        "channel"
    ]

    existing = await reminder_exists(
        training_id=training_id,
        reminder_type=reminder_type,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        channel=channel,
        scheduled_at=scheduled_at,
        db=db,
    )

    if existing:
        return None

    reminder = Reminder(
        training_id=training_id,
        reminder_type=reminder_type,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        channel=channel,
        scheduled_at=scheduled_at,
        status="PENDING",
    )

    db.add(reminder)

    return reminder


# ============================================================
# DOCUMENT STATUS
# ============================================================

async def get_document(
    training_id: int,
    document_type: str,
    db: AsyncSession,
):
    result = await db.execute(
        select(TrainingDocument).where(
            TrainingDocument.training_id
            == training_id,

            TrainingDocument.document_type
            == document_type,
        )
    )

    return result.scalar_one_or_none()


async def get_document_status(
    training_id: int,
    document_type: str,
    db: AsyncSession,
):
    document = await get_document(
        training_id,
        document_type,
        db,
    )

    if document is None:
        return "PENDING"

    return (
        str(document.status)
        .strip()
        .upper()
    )


def document_is_complete(
    status: str,
):
    return status in {
        "RECEIVED",
        "DONE",
    }


# ============================================================
# GET REQUIRED DOCUMENTS
# ============================================================

def get_required_documents(
    training: Training,
):
    """
    Return the documents required for this training.
    """

    documents = []

    if training.attendance_required:
        documents.append(
            "ATTENDANCE"
        )

    if training.ojt_required:
        documents.append(
            "OJT_REPORT"
        )

    return documents


# ============================================================
# NORMAL TRAINING REMINDERS
# ============================================================

async def get_training_reminders(
    training: Training,
    db: AsyncSession,
):
    """
    Generate pre-training reminders.

    Rules:
        7 days before
        2 days before
        1 day before

    Recipients are resolved from the training's
    Target Audience.
    """

    if training.status != "SCHEDULED":
        return []

    if getattr(
        training,
        "audience_id",
        None,
    ) is None:
        return []

    recipients = (
        await get_active_reminder_recipients(
            training,
            db,
        )
    )

    if not recipients:
        return []

    reminders_to_create = []

    now = datetime.now()

    for reminder_type, days_before in (
        PRE_TRAINING_RULES
    ):

        reminder_date = (
            training.scheduled_date
            - timedelta(
                days=days_before
            )
        )

        scheduled_at = datetime.combine(
            reminder_date,
            DEFAULT_SEND_TIME,
        )

        # Do not create reminders that are already
        # in the past.
        if scheduled_at <= now:
            continue

        for recipient in recipients:

            reminder = await create_reminder(
                training_id=training.id,

                reminder_type=(
                    reminder_type
                ),

                recipient=recipient,

                scheduled_at=(
                    scheduled_at
                ),

                db=db,
            )

            if reminder:
                reminders_to_create.append(
                    reminder
                )

    await db.commit()

    return reminders_to_create


# ============================================================
# POST-TRAINING REMINDERS
# ============================================================

async def create_post_training_reminders(
    training: Training,
    db: AsyncSession,
):
    """
    Generate post-training reminders after HR marks
    the training as COMPLETED.

    For every required document:

        Immediately
        +2 days
        +7 days

    After the +7 day reminder, the Celery worker can
    continue the weekly reminder cycle.

    Recipients are resolved from the training's
    Target Audience.
    """

    if training.status != "COMPLETED":
        return []

    if getattr(
        training,
        "audience_id",
        None,
    ) is None:
        return []

    required_documents = (
        get_required_documents(
            training
        )
    )

    if not required_documents:
        return []

    recipients = (
        await get_active_reminder_recipients(
            training,
            db,
        )
    )

    if not recipients:
        return []

    reminders_to_create = []

    completion_time = datetime.now()

    for document_type in required_documents:

        document_status = (
            await get_document_status(
                training.id,
                document_type,
                db,
            )
        )

        # Already complete -> no reminders.
        if document_is_complete(
            document_status
        ):
            continue

        for rule_name, days_after in (
            POST_TRAINING_RULES
        ):

            if days_after == 0:

                scheduled_at = (
                    completion_time
                )

            else:

                future_datetime = (
                    completion_time
                    + timedelta(
                        days=days_after
                    )
                )

                scheduled_at = (
                    datetime.combine(
                        future_datetime.date(),
                        DEFAULT_SEND_TIME,
                    )
                )

            reminder_type = (
                "POST_TRAINING_"
                f"{rule_name}_"
                f"{document_type}"
            )

            for recipient in recipients:

                reminder = (
                    await create_reminder(
                        training_id=training.id,

                        reminder_type=(
                            reminder_type
                        ),

                        recipient=recipient,

                        scheduled_at=(
                            scheduled_at
                        ),

                        db=db,
                    )
                )

                if reminder:
                    reminders_to_create.append(
                        reminder
                    )

    await db.commit()

    return reminders_to_create


# ============================================================
# CANCEL PENDING DOCUMENT REMINDERS
# ============================================================

async def cancel_document_reminders(
    training_id: int,
    document_type: str,
    db: AsyncSession,
):
    """
    Cancel all pending post-training reminders for
    one document.

    Called when HR submits Attendance or OJT.
    """

    result = await db.execute(
        select(Reminder).where(
            Reminder.training_id
            == training_id,

            Reminder.status
            == "PENDING",
        )
    )

    reminders = result.scalars().all()

    cancelled = 0

    for reminder in reminders:

        reminder_type = (
            reminder.reminder_type
            .strip()
            .upper()
        )

        if not reminder_type.startswith(
            "POST_TRAINING_"
        ):
            continue

        if not reminder_type.endswith(
            f"_{document_type}"
        ):
            continue

        reminder.status = (
            "CANCELLED"
        )

        reminder.failure_reason = (
            f"{document_type} submitted. "
            "Future reminder cancelled."
        )

        cancelled += 1

    await db.commit()

    return cancelled


# ============================================================
# CANCEL ALL POST-TRAINING REMINDERS
# ============================================================

async def cancel_all_post_training_reminders(
    training_id: int,
    db: AsyncSession,
):
    """
    Cancel all pending post-training reminders for
    a training.

    Used when every required document is complete.
    """

    result = await db.execute(
        select(Reminder).where(
            Reminder.training_id
            == training_id,

            Reminder.status
            == "PENDING",
        )
    )

    reminders = result.scalars().all()

    cancelled = 0

    for reminder in reminders:

        reminder_type = (
            reminder.reminder_type
            .strip()
            .upper()
        )

        if not reminder_type.startswith(
            "POST_TRAINING_"
        ):
            continue

        reminder.status = (
            "CANCELLED"
        )

        reminder.failure_reason = (
            "All required post-training "
            "documents submitted."
        )

        cancelled += 1

    await db.commit()

    return cancelled
