from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.training import Training
from app.models.training_document import TrainingDocument
from app.schemas.post_training import (
    DocumentStatusUpdate,
    PostTrainingResponse,
    TrainingConductedRequest,
)


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
# HELPER FUNCTIONS
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

    training = result.scalar_one_or_none()

    if training is None:
        raise HTTPException(
            status_code=404,
            detail=f"Training with ID {training_id} not found.",
        )

    return training


async def get_document(
    training_id: int,
    document_type: str,
    db: AsyncSession,
) -> TrainingDocument | None:

    result = await db.execute(
        select(TrainingDocument).where(
            TrainingDocument.training_id == training_id,
            TrainingDocument.document_type == document_type,
        )
    )

    return result.scalar_one_or_none()


# ============================================================
# 1. GET POST-TRAINING STATUS
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
    Get the complete post-training status.

    Returns:
    - Training status
    - Attendance requirement/status
    - OJT requirement/status
    """

    training = await get_training_or_404(
        training_id,
        db,
    )

    documents_result = await db.execute(
        select(TrainingDocument).where(
            TrainingDocument.training_id == training_id
        )
    )

    documents = documents_result.scalars().all()

    attendance_status = None
    ojt_status = None

    for document in documents:

        document_type = (
            str(document.document_type)
            .strip()
            .upper()
        )

        if document_type == "ATTENDANCE":
            attendance_status = document.status

        elif document_type == "OJT_REPORT":
            ojt_status = document.status

    return PostTrainingResponse(
        training_id=training.id,
        training_name=training.training_name,
        scheduled_date=training.scheduled_date,
        status=training.status,
        attendance_required=training.attendance_required,
        ojt_required=training.ojt_required,
        attendance_status=attendance_status,
        ojt_status=ojt_status,
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
    Mark a training as conducted or not conducted.

    YES:
        Training → COMPLETED
        Attendance document → PENDING
        OJT document → PENDING if required

    NO:
        Training → NOT_CONDUCTED
        Reason is required
    """

    training = await get_training_or_404(
        training_id,
        db,
    )

    # ========================================================
    # YES — TRAINING WAS CONDUCTED
    # ========================================================

    if data.conducted is True:

        training.status = "COMPLETED"

        # ----------------------------------------------------
        # Attendance document
        # ----------------------------------------------------

        if training.attendance_required:

            attendance = await get_document(
                training_id,
                "ATTENDANCE",
                db,
            )

            if attendance is None:

                attendance = TrainingDocument(
                    training_id=training_id,
                    document_type="ATTENDANCE",
                    status="PENDING",
                )

                db.add(attendance)

            else:

                # Don't overwrite an already received document.
                if attendance.status not in {
                    "RECEIVED",
                    "DONE",
                }:
                    attendance.status = "PENDING"

        # ----------------------------------------------------
        # OJT document
        # ----------------------------------------------------

        if training.ojt_required:

            ojt = await get_document(
                training_id,
                "OJT_REPORT",
                db,
            )

            if ojt is None:

                ojt = TrainingDocument(
                    training_id=training_id,
                    document_type="OJT_REPORT",
                    status="PENDING",
                )

                db.add(ojt)

            else:

                if ojt.status not in {
                    "RECEIVED",
                    "DONE",
                }:
                    ojt.status = "PENDING"

        await db.commit()

        return {
            "success": True,
            "message": "Training marked as conducted.",
            "training_id": training_id,
            "status": "COMPLETED",
            "attendance_required": (
                training.attendance_required
            ),
            "ojt_required": (
                training.ojt_required
            ),
            "next_action": (
                "Submit attendance and OJT documents "
                "where applicable."
            ),
        }

    # ========================================================
    # NO — TRAINING WAS NOT CONDUCTED
    # ========================================================

    if not data.reason or not data.reason.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "A reason is required when "
                "training was not conducted."
            ),
        )

    training.status = "NOT_CONDUCTED"

    training.not_conducted_reason = (
        data.reason.strip()
    )

    await db.commit()

    return {
        "success": True,
        "message": (
            "Training marked as not conducted."
        ),
        "training_id": training_id,
        "status": "NOT_CONDUCTED",
        "reason": training.not_conducted_reason,
        "next_action": (
            "HOD should communicate the "
            "rescheduled date to HR."
        ),
    }


# ============================================================
# 3. UPDATE ATTENDANCE / OJT DOCUMENT STATUS
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
    Update attendance or OJT document status.

    Supported document types:
        ATTENDANCE
        OJT_REPORT

    Supported statuses:
        PENDING
        RECEIVED
        DONE

    received_via examples:
        WHATSAPP
        EMAIL
        MANUAL
        UPLOAD
    """

    # --------------------------------------------------------
    # Normalize document type
    # --------------------------------------------------------

    document_type = str(
        document_type
    ).strip().upper()

    if document_type not in DOCUMENT_TYPES:

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid document type.",
                "received": document_type,
                "allowed": sorted(
                    DOCUMENT_TYPES
                ),
            },
        )

    # --------------------------------------------------------
    # Normalize status
    # --------------------------------------------------------

    raw_status = data.status

    if raw_status is None:

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Document status is required.",
                "allowed": sorted(
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
                "error": "Invalid document status.",
                "received": raw_status,
                "normalized": status,
                "allowed": sorted(
                    DOCUMENT_STATUSES
                ),
            },
        )

    # --------------------------------------------------------
    # Normalize received_via
    # --------------------------------------------------------

    received_via = None

    if data.received_via:

        received_via = str(
            data.received_via
        ).strip().upper()

    # --------------------------------------------------------
    # Clean remarks
    # --------------------------------------------------------

    remarks = None

    if data.remarks:

        remarks = str(
            data.remarks
        ).strip()

    # --------------------------------------------------------
    # Check training
    # --------------------------------------------------------

    training = await get_training_or_404(
        training_id,
        db,
    )

    # --------------------------------------------------------
    # Find existing document
    # --------------------------------------------------------

    document = await get_document(
        training_id,
        document_type,
        db,
    )

    # --------------------------------------------------------
    # Create document if it doesn't exist
    # --------------------------------------------------------

    if document is None:

        document = TrainingDocument(
            training_id=training_id,
            document_type=document_type,
            status=status,
        )

        db.add(document)

    else:

        document.status = status

    # --------------------------------------------------------
    # Update received information
    # --------------------------------------------------------

    if received_via:

        document.received_via = received_via

    if remarks:

        document.remarks = remarks

    # --------------------------------------------------------
    # Record received time
    # --------------------------------------------------------

    if status in {
        "RECEIVED",
        "DONE",
    }:

        document.received_at = datetime.utcnow()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    await db.commit()

    await db.refresh(document)

    return {
        "success": True,
        "message": (
            f"{document_type} status updated successfully."
        ),
        "training_id": training_id,
        "training_name": training.training_name,
        "document_type": document_type,
        "status": document.status,
        "received_via": document.received_via,
        "received_at": document.received_at,
        "remarks": document.remarks,
    }


# ============================================================
# 4. GET DOCUMENTS FOR A TRAINING
# ============================================================

@router.get(
    "/{training_id}/documents",
)
async def get_training_documents(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all attendance/OJT documents associated
    with a training.
    """

    await get_training_or_404(
        training_id,
        db,
    )

    result = await db.execute(
        select(TrainingDocument)
        .where(
            TrainingDocument.training_id
            == training_id
        )
        .order_by(
            TrainingDocument.document_type
        )
    )

    documents = result.scalars().all()

    return {
        "training_id": training_id,
        "documents": [
            {
                "id": document.id,
                "document_type": document.document_type,
                "status": document.status,
                "file_path": document.file_path,
                "received_via": document.received_via,
                "received_at": document.received_at,
                "remarks": document.remarks,
                "created_at": document.created_at,
            }
            for document in documents
        ],
    }