from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

from app.models.training import Training
from app.models.training_document import TrainingDocument
from app.models.reminder import Reminder

from app.schemas.post_training import (
    DocumentStatusUpdate,
    PostTrainingResponse,
    TrainingConductedRequest,
)

from app.services.reminder_engine import (
    create_post_training_reminders,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/post-training",
    tags=["Post Training"],
)


# ============================================================
# CONSTANTS
# ============================================================

DOCUMENT_TYPES = {
    "ATTENDANCE",
    "OJT_REPORT",
}

DOCUMENT_STATUSES = {
    "PENDING",
    "RECEIVED",
    "DONE",
}


# ============================================================
# HELPER — GET TRAINING
# ============================================================

async def get_training_or_404(
    training_id: int,
    db: AsyncSession,
) -> Training:

    result = await db.execute(
        select(Training).where(
            Training.id == training_id
        )
    )

    training = (
        result.scalar_one_or_none()
    )

    if training is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Training with ID "
                f"{training_id} not found."
            ),
        )

    return training


# ============================================================
# HELPER — GET DOCUMENT
# ============================================================

async def get_document(
    training_id: int,
    document_type: str,
    db: AsyncSession,
) -> TrainingDocument | None:

    result = await db.execute(
        select(TrainingDocument).where(
            TrainingDocument.training_id
            == training_id,

            TrainingDocument.document_type
            == document_type,
        )
    )

    return (
        result.scalar_one_or_none()
    )


# ============================================================
# HELPER — DOCUMENT COMPLETE
# ============================================================

def document_is_complete(
    document: TrainingDocument | None,
) -> bool:

    if document is None:
        return False

    status = (
        str(document.status)
        .strip()
        .upper()
    )

    return status in {
        "RECEIVED",
        "DONE",
    }


# ============================================================
# HELPER — GET DOCUMENT STATUS
# ============================================================

def get_document_status(
    document: TrainingDocument | None,
):

    if document is None:
        return "PENDING"

    return (
        str(document.status)
        .strip()
        .upper()
    )


# ============================================================
# HELPER — CANCEL DOCUMENT REMINDERS
# ============================================================

async def cancel_document_reminders(
    training_id: int,
    document_type: str,
    db: AsyncSession,
):
    """
    Cancel all pending post-training reminders
    belonging to a particular document.

    Example:

        Attendance submitted
            ↓
        Cancel future Attendance reminders

    OJT reminders are NOT cancelled unless
    OJT is also submitted.
    """

    result = await db.execute(
        select(Reminder).where(
            Reminder.training_id
            == training_id,

            Reminder.status
            == "PENDING",
        )
    )

    reminders = (
        result.scalars().all()
    )

    cancelled = 0

    target_suffix = (
        f"_{document_type}"
    )

    for reminder in reminders:

        reminder_type = (
            str(reminder.reminder_type)
            .strip()
            .upper()
        )

        # ----------------------------------------------------
        # Only post-training reminders
        # ----------------------------------------------------

        if not reminder_type.startswith(
            "POST_TRAINING_"
        ):
            continue

        # ----------------------------------------------------
        # Only matching document
        # ----------------------------------------------------

        if not reminder_type.endswith(
            target_suffix
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

    return cancelled


# ============================================================
# HELPER — CANCEL ALL POST TRAINING REMINDERS
# ============================================================

async def cancel_all_post_training_reminders(
    training_id: int,
    db: AsyncSession,
):
    """
    Cancel every pending post-training reminder
    for a training.

    Used when all required documents are complete.
    """

    result = await db.execute(
        select(Reminder).where(
            Reminder.training_id
            == training_id,

            Reminder.status
            == "PENDING",
        )
    )

    reminders = (
        result.scalars().all()
    )

    cancelled = 0

    for reminder in reminders:

        reminder_type = (
            str(reminder.reminder_type)
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

    return cancelled


# ============================================================
# HELPER — CHECK ALL REQUIRED DOCUMENTS
# ============================================================

async def check_all_required_documents_complete(
    training: Training,
    db: AsyncSession,
) -> bool:
    """
    Returns True only when every required
    document has been submitted.
    """

    # --------------------------------------------------------
    # Attendance
    # --------------------------------------------------------

    if training.attendance_required:

        attendance = await get_document(
            training.id,
            "ATTENDANCE",
            db,
        )

        if not document_is_complete(
            attendance
        ):
            return False

    # --------------------------------------------------------
    # OJT
    # --------------------------------------------------------

    if training.ojt_required:

        ojt = await get_document(
            training.id,
            "OJT_REPORT",
            db,
        )

        if not document_is_complete(
            ojt
        ):
            return False

    # --------------------------------------------------------
    # No outstanding documents
    # --------------------------------------------------------

    return True


# ============================================================
# 1. GET POST TRAINING STATUS
# ============================================================

@router.get(
    "/{training_id}",
    response_model=PostTrainingResponse,
)
async def get_post_training_status(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Return complete post-training status.

    Includes:

        Training status
        Attendance requirement
        Attendance status
        OJT requirement
        OJT status
    """

    training = await get_training_or_404(
        training_id,
        db,
    )

    documents_result = await db.execute(
        select(TrainingDocument).where(
            TrainingDocument.training_id
            == training_id
        )
    )

    documents = (
        documents_result
        .scalars()
        .all()
    )

    attendance_status = None
    ojt_status = None

    for document in documents:

        document_type = (
            str(document.document_type)
            .strip()
            .upper()
        )

        if document_type == "ATTENDANCE":

            attendance_status = (
                document.status
            )

        elif document_type == "OJT_REPORT":

            ojt_status = (
                document.status
            )

    return PostTrainingResponse(
        training_id=training.id,

        training_name=(
            training.training_name
        ),

        scheduled_date=(
            training.scheduled_date
        ),

        status=training.status,

        attendance_required=(
            training.attendance_required
        ),

        ojt_required=(
            training.ojt_required
        ),

        attendance_status=(
            attendance_status
        ),

        ojt_status=(
            ojt_status
        ),
    )


# ============================================================
# 2. MARK TRAINING CONDUCTED / NOT CONDUCTED
# ============================================================

@router.post(
    "/{training_id}/conducted",
)
async def mark_training_conducted(
    training_id: int,
    data: TrainingConductedRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark training as:

        COMPLETED

    or:

        NOT_CONDUCTED

    When COMPLETED:

        Attendance → PENDING
        OJT → PENDING if required

        Then create:

        Immediate reminder
        +2 days reminder
        +7 days reminder

        Weekly reminders are generated
        by Celery after the +7 reminder
        is successfully sent.
    """

    training = await get_training_or_404(
        training_id,
        db,
    )

    # ========================================================
    # TRAINING CONDUCTED
    # ========================================================

    if data.conducted is True:

        training.status = "COMPLETED"

        # ----------------------------------------------------
        # Attendance
        # ----------------------------------------------------

        if training.attendance_required:

            attendance = await get_document(
                training_id,
                "ATTENDANCE",
                db,
            )

            if attendance is None:

                attendance = TrainingDocument(
                    training_id=(
                        training_id
                    ),

                    document_type=(
                        "ATTENDANCE"
                    ),

                    status="PENDING",
                )

                db.add(attendance)

            else:

                existing_status = (
                    str(
                        attendance.status
                    )
                    .strip()
                    .upper()
                )

                # Never overwrite a submitted
                # document.

                if existing_status not in {
                    "RECEIVED",
                    "DONE",
                }:

                    attendance.status = (
                        "PENDING"
                    )

        # ----------------------------------------------------
        # OJT Report
        # ----------------------------------------------------

        if training.ojt_required:

            ojt = await get_document(
                training_id,
                "OJT_REPORT",
                db,
            )

            if ojt is None:

                ojt = TrainingDocument(
                    training_id=(
                        training_id
                    ),

                    document_type=(
                        "OJT_REPORT"
                    ),

                    status="PENDING",
                )

                db.add(ojt)

            else:

                existing_status = (
                    str(
                        ojt.status
                    )
                    .strip()
                    .upper()
                )

                if existing_status not in {
                    "RECEIVED",
                    "DONE",
                }:

                    ojt.status = (
                        "PENDING"
                    )

        # ----------------------------------------------------
        # SAVE TRAINING + DOCUMENTS
        # ----------------------------------------------------

        await db.commit()

        # ----------------------------------------------------
        # Refresh the object.
        #
        # Important for AsyncSession:
        # after commit SQLAlchemy can expire
        # object attributes.
        # ----------------------------------------------------

        await db.refresh(
            training
        )

        # ----------------------------------------------------
        # CREATE POST TRAINING REMINDERS
        # ----------------------------------------------------

        post_training_reminders = (
            await create_post_training_reminders(
                training,
                db,
            )
        )

        # ----------------------------------------------------
        # Count
        # ----------------------------------------------------

        reminder_count = len(
            post_training_reminders
        )

        # ----------------------------------------------------
        # Get latest document statuses
        # ----------------------------------------------------

        attendance = (
            await get_document(
                training_id,
                "ATTENDANCE",
                db,
            )
        )

        ojt = (
            await get_document(
                training_id,
                "OJT_REPORT",
                db,
            )
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {
            "success": True,

            "message": (
                "Training marked as conducted."
            ),

            "training_id": training_id,

            "status": "COMPLETED",

            "attendance_required": (
                training.attendance_required
            ),

            "attendance_status": (
                get_document_status(
                    attendance
                )
            ),

            "ojt_required": (
                training.ojt_required
            ),

            "ojt_status": (
                get_document_status(
                    ojt
                )
            ),

            "post_training_reminders_created":
                reminder_count,

            "reminder_schedule": [
                "IMMEDIATE",
                "2_DAYS",
                "7_DAYS",
                "WEEKLY_UNTIL_SUBMITTED",
            ],

            "next_action": (
                "Submit required attendance "
                "and OJT documents."
            ),
        }

    # ========================================================
    # TRAINING NOT CONDUCTED
    # ========================================================

    if (
        not data.reason
        or not data.reason.strip()
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "A reason is required when "
                "training was not conducted."
            ),
        )

    training.status = (
        "NOT_CONDUCTED"
    )

    training.not_conducted_reason = (
        data.reason.strip()
    )

    await db.commit()

    return {
        "success": True,

        "message": (
            "Training marked as "
            "not conducted."
        ),

        "training_id": training_id,

        "status": "NOT_CONDUCTED",

        "reason": (
            training.not_conducted_reason
        ),

        "next_action": (
            "HR should reschedule the "
            "training if required."
        ),
    }


# ============================================================
# 3. UPDATE ATTENDANCE / OJT STATUS
# ============================================================

@router.patch(
    "/{training_id}/documents/{document_type}",
)
async def update_document_status(
    training_id: int,
    document_type: str,
    data: DocumentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update Attendance or OJT status.

    Example:

        PATCH
        /api/post-training/11/documents/ATTENDANCE

    Body:

        {
            "status": "DONE",
            "received_via": "EMAIL",
            "remarks": "Received from HOD"
        }

    When status becomes RECEIVED or DONE:

        Future reminders for that document
        are immediately cancelled.

    If every required document is complete:

        All remaining post-training
        reminders are cancelled.
    """

    # ========================================================
    # NORMALIZE DOCUMENT TYPE
    # ========================================================

    document_type = str(
        document_type
    ).strip().upper()

    if document_type not in DOCUMENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail={
                "error":
                    "Invalid document type.",

                "received":
                    document_type,

                "allowed":
                    sorted(
                        DOCUMENT_TYPES
                    ),
            },
        )

    # ========================================================
    # NORMALIZE STATUS
    # ========================================================

    raw_status = data.status

    if raw_status is None:

        raise HTTPException(
            status_code=400,
            detail={
                "error":
                    "Document status is required.",

                "allowed":
                    sorted(
                        DOCUMENT_STATUSES
                    ),
            },
        )

    status = str(
        raw_status
    ).strip().upper()

    if status not in DOCUMENT_STATUSES:

        raise HTTPException(
            status_code=400,
            detail={
                "error":
                    "Invalid document status.",

                "received":
                    raw_status,

                "normalized":
                    status,

                "allowed":
                    sorted(
                        DOCUMENT_STATUSES
                    ),
            },
        )

    # ========================================================
    # GET TRAINING
    # ========================================================

    training = await get_training_or_404(
        training_id,
        db,
    )

    # ========================================================
    # VALIDATE REQUIREMENT
    # ========================================================

    if (
        document_type == "ATTENDANCE"
        and not training.attendance_required
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Attendance is not required "
                "for this training."
            ),
        )

    if (
        document_type == "OJT_REPORT"
        and not training.ojt_required
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "OJT report is not required "
                "for this training."
            ),
        )

    # ========================================================
    # RECEIVED VIA
    # ========================================================

    received_via = None

    if data.received_via:

        received_via = str(
            data.received_via
        ).strip().upper()

    # ========================================================
    # REMARKS
    # ========================================================

    remarks = None

    if data.remarks:

        remarks = str(
            data.remarks
        ).strip()

    # ========================================================
    # GET EXISTING DOCUMENT
    # ========================================================

    document = await get_document(
        training_id,
        document_type,
        db,
    )

    # ========================================================
    # CREATE IF MISSING
    # ========================================================

    if document is None:

        document = TrainingDocument(
            training_id=training_id,

            document_type=document_type,

            status=status,
        )

        db.add(document)

    else:

        document.status = status

    # ========================================================
    # RECEIVED VIA
    # ========================================================

    if received_via:

        document.received_via = (
            received_via
        )

    # ========================================================
    # REMARKS
    # ========================================================

    if remarks:

        document.remarks = (
            remarks
        )

    # ========================================================
    # RECEIVED TIMESTAMP
    # ========================================================

    if status in {
        "RECEIVED",
        "DONE",
    }:

        document.received_at = (
            datetime.utcnow()
        )

    elif status == "PENDING":

        # If HR moves a document back
        # to PENDING, clear received time.

        document.received_at = None

    # ========================================================
    # SAVE DOCUMENT
    # ========================================================

    await db.commit()

    await db.refresh(
        document
    )

    # ========================================================
    # CANCEL REMINDERS WHEN SUBMITTED
    # ========================================================

    cancelled_reminders = 0

    if status in {
        "RECEIVED",
        "DONE",
    }:

        cancelled_reminders = (
            await cancel_document_reminders(
                training_id=training_id,

                document_type=(
                    document_type
                ),

                db=db,
            )
        )

        # ----------------------------------------------------
        # Save cancellation
        # ----------------------------------------------------

        await db.commit()

    # ========================================================
    # CHECK ALL REQUIRED DOCUMENTS
    # ========================================================

    all_complete = (
        await check_all_required_documents_complete(
            training,
            db,
        )
    )

    cancelled_all = 0

    if all_complete:

        cancelled_all = (
            await cancel_all_post_training_reminders(
                training_id=training_id,
                db=db,
            )
        )

        await db.commit()

    # ========================================================
    # REFRESH DOCUMENT
    # ========================================================

    await db.refresh(
        document
    )

    # ========================================================
    # GET CURRENT ATTENDANCE
    # ========================================================

    attendance = (
        await get_document(
            training_id,
            "ATTENDANCE",
            db,
        )
    )

    # ========================================================
    # GET CURRENT OJT
    # ========================================================

    ojt = (
        await get_document(
            training_id,
            "OJT_REPORT",
            db,
        )
    )

    # ========================================================
    # DETERMINE NEXT ACTION
    # ========================================================

    if all_complete:

        next_action = (
            "All required post-training "
            "documents have been submitted. "
            "All future reminders stopped."
        )

    elif (
        training.attendance_required
        and not document_is_complete(
            attendance
        )
    ):

        next_action = (
            "Attendance submission is "
            "still pending."
        )

    elif (
        training.ojt_required
        and not document_is_complete(
            ojt
        )
    ):

        next_action = (
            "OJT report submission is "
            "still pending."
        )

    else:

        next_action = (
            "Review remaining "
            "post-training requirements."
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "success": True,

        "message": (
            f"{document_type} status "
            "updated successfully."
        ),

        "training_id":
            training_id,

        "training_name":
            training.training_name,

        "document_type":
            document_type,

        "status":
            document.status,

        "received_via":
            document.received_via,

        "received_at":
            document.received_at,

        "remarks":
            document.remarks,

        "cancelled_reminders":
            cancelled_reminders,

        "all_documents_complete":
            all_complete,

        "remaining_reminders_cancelled":
            cancelled_all,

        "attendance_status":
            get_document_status(
                attendance
            ),

        "ojt_status":
            get_document_status(
                ojt
            ),

        "next_action":
            next_action,
    }


# ============================================================
# 4. GET ALL DOCUMENTS
# ============================================================

@router.get(
    "/{training_id}/documents",
)
async def get_training_documents(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all Attendance/OJT documents
    for a training.
    """

    await get_training_or_404(
        training_id,
        db,
    )

    result = await db.execute(
        select(
            TrainingDocument
        )
        .where(
            TrainingDocument.training_id
            == training_id
        )
        .order_by(
            TrainingDocument.document_type
        )
    )

    documents = (
        result.scalars().all()
    )

    return {
        "training_id":
            training_id,

        "documents": [
            {
                "id":
                    document.id,

                "document_type":
                    document.document_type,

                "status":
                    document.status,

                "file_path":
                    document.file_path,

                "received_via":
                    document.received_via,

                "received_at":
                    document.received_at,

                "remarks":
                    document.remarks,

                "created_at":
                    document.created_at,
            }

            for document in documents
        ],
    }