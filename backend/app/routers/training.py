from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.training import Training
from app.schemas.training import (
    TrainingCreate,
    TrainingResponse,
    TrainingReschedule,
    TrainingStatusUpdate,
    TrainingUpdate,
)


router = APIRouter(
    prefix="/api/trainings",
    tags=["Training Management"],
)


VALID_STATUSES = {
    "SCHEDULED",
    "COMPLETED",
    "PENDING",
    "NOT_CONDUCTED",
    "RESCHEDULED",
}


# ==================================================
# GET ALL TRAININGS
# ==================================================

@router.get(
    "",
    response_model=list[TrainingResponse],
)
async def get_trainings(
    db: AsyncSession = Depends(get_db),
    department_id: int | None = None,
    status: str | None = None,
):
    query = select(Training).order_by(
        Training.scheduled_date
    )

    if department_id is not None:
        query = query.where(
            Training.department_id == department_id
        )

    if status is not None:

        status = status.upper()

        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid training status: {status}",
            )

        query = query.where(
            Training.status == status
        )

    result = await db.execute(query)

    return result.scalars().all()


# ==================================================
# GET MONTHLY TRAININGS
# ==================================================

@router.get(
    "/calendar",
    response_model=list[TrainingResponse],
)
async def get_calendar_trainings(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    start_date = date(
        year,
        month,
        1,
    )

    if month == 12:

        end_date = date(
            year + 1,
            1,
            1,
        )

    else:

        end_date = date(
            year,
            month + 1,
            1,
        )

    query = (
        select(Training)
        .where(
            Training.scheduled_date >= start_date,
            Training.scheduled_date < end_date,
        )
        .order_by(
            Training.scheduled_date,
            Training.scheduled_time,
        )
    )

    result = await db.execute(query)

    return result.scalars().all()


# ==================================================
# GET SINGLE TRAINING
# ==================================================

@router.get(
    "/{training_id}",
    response_model=TrainingResponse,
)
async def get_training(
    training_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Training).where(
            Training.id == training_id
        )
    )

    training = result.scalar_one_or_none()

    if not training:

        raise HTTPException(
            status_code=404,
            detail="Training not found.",
        )

    return training


# ==================================================
# CREATE TRAINING
# ==================================================

@router.post(
    "",
    response_model=TrainingResponse,
    status_code=201,
)
async def create_training(
    training_data: TrainingCreate,
    db: AsyncSession = Depends(get_db),
):
    training = Training(
        training_name=training_data.training_name,
        training_type=training_data.training_type,
        department_id=training_data.department_id,
        scheduled_date=training_data.scheduled_date,
        scheduled_time=training_data.scheduled_time,
        status="SCHEDULED",
        is_department_wise=training_data.is_department_wise,
        attendance_required=training_data.attendance_required,
        ojt_required=training_data.ojt_required,
        trainer_name=training_data.trainer_name,
    )

    db.add(training)

    await db.commit()
    await db.refresh(training)

    return training


# ==================================================
# UPDATE TRAINING
# ==================================================

@router.put(
    "/{training_id}",
    response_model=TrainingResponse,
)
async def update_training(
    training_id: int,
    training_data: TrainingUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Training).where(
            Training.id == training_id
        )
    )

    training = result.scalar_one_or_none()

    if not training:

        raise HTTPException(
            status_code=404,
            detail="Training not found.",
        )

    update_data = training_data.model_dump(
        exclude_unset=True
    )

    if "status" in update_data:

        status = update_data["status"].upper()

        if status not in VALID_STATUSES:

            raise HTTPException(
                status_code=400,
                detail=f"Invalid training status: {status}",
            )

        update_data["status"] = status

    for field, value in update_data.items():

        setattr(
            training,
            field,
            value,
        )

    await db.commit()
    await db.refresh(training)

    return training


# ==================================================
# RESCHEDULE TRAINING
# ==================================================

@router.patch(
    "/{training_id}/reschedule",
    response_model=TrainingResponse,
)
async def reschedule_training(
    training_id: int,
    data: TrainingReschedule,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Training).where(
            Training.id == training_id
        )
    )

    training = result.scalar_one_or_none()

    if not training:

        raise HTTPException(
            status_code=404,
            detail="Training not found.",
        )

    # Preserve the original date only once
    if training.original_date is None:

        training.original_date = (
            training.scheduled_date
        )

    training.rescheduled_date = data.new_date

    training.scheduled_date = data.new_date

    training.reschedule_reason = data.reason

    training.status = "RESCHEDULED"

    await db.commit()
    await db.refresh(training)

    return training


# ==================================================
# UPDATE TRAINING STATUS
# ==================================================

@router.patch(
    "/{training_id}/status",
    response_model=TrainingResponse,
)
async def update_training_status(
    training_id: int,
    data: TrainingStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Training).where(
            Training.id == training_id
        )
    )

    training = result.scalar_one_or_none()

    if not training:

        raise HTTPException(
            status_code=404,
            detail="Training not found.",
        )

    status = data.status.upper()

    if status not in VALID_STATUSES:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid training status: {status}",
        )

    training.status = status

    if status == "NOT_CONDUCTED":

        training.not_conducted_reason = (
            data.reason
        )

    await db.commit()
    await db.refresh(training)

    return training