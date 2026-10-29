from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

from app.models.training import Training
from app.services.reminder_engine import get_training_reminders

from app.schemas.training import (

    TrainingCreate,

    TrainingResponse,

    TrainingReschedule,

    TrainingStatusUpdate,

    TrainingUpdate,

)

router = APIRouter(

    prefix="/api/trainings",

    tags=["Trainings"],

)

VALID_STATUSES = {

    "SCHEDULED",

    "COMPLETED",

    "PENDING",

    "NOT_CONDUCTED",

    "RESCHEDULED",

}

# ============================================================

# GET ALL TRAININGS

# ============================================================

@router.get("/")

async def get_trainings(

    department_id: int | None = None,

    status: str | None = None,

    db: AsyncSession = Depends(get_db),

):

    query = select(Training).order_by(

        Training.scheduled_date.desc(),

        Training.id.desc(),

    )

    if department_id is not None:

        query = query.where(

            Training.department_id == department_id

        )

    if status:

        normalized_status = status.strip().upper()

        if normalized_status not in VALID_STATUSES:

            raise HTTPException(

                status_code=400,

                detail=(

                    f"Invalid status '{status}'. "

                    f"Allowed values: "

                    f"{', '.join(sorted(VALID_STATUSES))}"

                ),

            )

        query = query.where(

            Training.status == normalized_status

        )

    result = await db.execute(query)

    trainings = result.scalars().all()

    return {

        "value": [

            {

                "id": training.id,

                "training_name": training.training_name,

                "training_type": training.training_type,

                "department_id": training.department_id,

                "audience_id": getattr(

                    training,

                    "audience_id",

                    None,

                ),

                "scheduled_date": training.scheduled_date,

                "training_to_date": getattr(

                    training,

                    "training_to_date",

                    None,

                ),

                "scheduled_time": training.scheduled_time,

                "duration_hours": getattr(

                    training,

                    "duration_hours",

                    None,

                ),

                "venue": getattr(

                    training,

                    "venue",

                    None,

                ),

                "status": training.status,

                "is_department_wise":

                    training.is_department_wise,

                "attendance_required":

                    training.attendance_required,

                "ojt_required":

                    training.ojt_required,

                "trainer_name":

                    training.trainer_name,

                "original_date":

                    training.original_date,

                "rescheduled_date":

                    training.rescheduled_date,

                "reschedule_reason":

                    training.reschedule_reason,

                "not_conducted_reason":

                    training.not_conducted_reason,

            }

            for training in trainings

        ],

        "Count": len(trainings),

    }

# ============================================================

# CALENDAR

# ============================================================

@router.get("/calendar")

async def get_training_calendar(

    year: int,

    month: int,

    db: AsyncSession = Depends(get_db),

):

    if month < 1 or month > 12:

        raise HTTPException(

            status_code=400,

            detail="Month must be between 1 and 12.",

        )

    query = select(Training).where(

        Training.scheduled_date.is_not(None)

    )

    result = await db.execute(query)

    trainings = result.scalars().all()

    filtered = [

        training

        for training in trainings

        if training.scheduled_date

        and training.scheduled_date.year == year

        and training.scheduled_date.month == month

    ]

    return {

        "value": [

            {

                "id": training.id,

                "training_name":

                    training.training_name,

                "training_type":

                    training.training_type,

                "department_id":

                    training.department_id,

                "audience_id":

                    getattr(

                        training,

                        "audience_id",

                        None,

                    ),

                "scheduled_date":

                    training.scheduled_date,

                "scheduled_time":

                    training.scheduled_time,

                "status":

                    training.status,

                "trainer_name":

                    training.trainer_name,

            }

            for training in filtered

        ],

        "Count": len(filtered),

    }

# ============================================================

# GET ONE TRAINING

# ============================================================

@router.get("/{training_id}")

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

    if training is None:

        raise HTTPException(

            status_code=404,

            detail="Training not found.",

        )

    return {

        "id": training.id,

        "training_name":

            training.training_name,

        "training_type":

            training.training_type,

        "department_id":

            training.department_id,

        "audience_id":

            getattr(

                training,

                "audience_id",

                None,

            ),

        "scheduled_date":

            training.scheduled_date,

        "training_to_date":

            getattr(

                training,

                "training_to_date",

                None,

            ),

        "scheduled_time":

            training.scheduled_time,

        "duration_hours":

            getattr(

                training,

                "duration_hours",

                None,

            ),

        "venue":

            getattr(

                training,

                "venue",

                None,

            ),

        "status":

            training.status,

        "is_department_wise":

            training.is_department_wise,

        "attendance_required":

            training.attendance_required,

        "ojt_required":

            training.ojt_required,

        "trainer_name":

            training.trainer_name,

        "original_date":

            training.original_date,

        "rescheduled_date":

            training.rescheduled_date,

        "reschedule_reason":

            training.reschedule_reason,

        "not_conducted_reason":

            training.not_conducted_reason,

        "created_at":

            training.created_at,

        "updated_at":

            training.updated_at,

    }

# ============================================================

# CREATE TRAINING

# ============================================================

@router.post("/")

async def create_training(

    data: TrainingCreate,

    db: AsyncSession = Depends(get_db),

):

    if not data.training_name.strip():

        raise HTTPException(

            status_code=400,

            detail="Training name is required.",

        )

    if data.scheduled_date is None:

        raise HTTPException(

            status_code=400,

            detail="Training date is required.",

        )

    if data.department_id is None:

        raise HTTPException(

            status_code=400,

            detail="Department is required.",

        )

    if data.audience_id is None:

        raise HTTPException(

            status_code=400,

            detail="Target audience is required.",

        )

    if data.training_to_date:

        if data.training_to_date < data.scheduled_date:

            raise HTTPException(

                status_code=400,

                detail=(

                    "Training end date cannot be "

                    "before the start date."

                ),

            )

    now = datetime.utcnow()

    training = Training(

        training_name=data.training_name.strip(),

        training_type=(

            data.training_type.strip()

            if data.training_type

            else None

        ),

        department_id=data.department_id,

        audience_id=data.audience_id,

        scheduled_date=data.scheduled_date,

        training_to_date=data.training_to_date,

        scheduled_time=data.scheduled_time,

        duration_hours=data.duration_hours,

        venue=(

            data.venue.strip()

            if data.venue

            else None

        ),

        status="SCHEDULED",

        is_department_wise=

            data.is_department_wise,

        attendance_required=

            data.attendance_required,

        ojt_required=

            data.ojt_required,

        trainer_name=(

            data.trainer_name.strip()

            if data.trainer_name

            else None

        ),

        created_at=now,

        updated_at=now,

    )

    db.add(training)

    await db.commit()
    await db.refresh(training)

    # Generate reminders automatically after the training is saved.
    reminders = await get_training_reminders(training, db)

    return {
        "success": True,
        "message": "Training created successfully.",
        "id": training.id,
        "reminders_created": len(reminders),

        "training": {

            "id": training.id,

            "training_name":

                training.training_name,

            "training_type":

                training.training_type,

            "department_id":

                training.department_id,

            "audience_id":

                training.audience_id,

            "scheduled_date":

                training.scheduled_date,

            "training_to_date":

                training.training_to_date,

            "scheduled_time":

                training.scheduled_time,

            "duration_hours":

                training.duration_hours,

            "venue":

                training.venue,

            "status":

                training.status,

            "is_department_wise":

                training.is_department_wise,

            "attendance_required":

                training.attendance_required,

            "ojt_required":

                training.ojt_required,

            "trainer_name":

                training.trainer_name,

        },

    }

# ============================================================

# UPDATE TRAINING

# ============================================================

@router.put("/{training_id}")

async def update_training(

    training_id: int,

    data: TrainingUpdate,

    db: AsyncSession = Depends(get_db),

):

    result = await db.execute(

        select(Training).where(

            Training.id == training_id

        )

    )

    training = result.scalar_one_or_none()

    if training is None:

        raise HTTPException(

            status_code=404,

            detail="Training not found.",

        )

    update_data = data.model_dump(

        exclude_unset=True

    )

    if (

        "training_name" in update_data

        and update_data["training_name"]

    ):

        training.training_name = (

            update_data["training_name"].strip()

        )

    if "training_type" in update_data:

        training.training_type = (

            update_data["training_type"].strip()

            if update_data["training_type"]

            else None

        )

    if "department_id" in update_data:

        training.department_id = (

            update_data["department_id"]

        )

    if "audience_id" in update_data:

        training.audience_id = (

            update_data["audience_id"]

        )

    if "scheduled_date" in update_data:

        training.scheduled_date = (

            update_data["scheduled_date"]

        )

    if "training_to_date" in update_data:

        training.training_to_date = (

            update_data["training_to_date"]

        )

    if "scheduled_time" in update_data:

        training.scheduled_time = (

            update_data["scheduled_time"]

        )

    if "duration_hours" in update_data:

        training.duration_hours = (

            update_data["duration_hours"]

        )

    if "venue" in update_data:

        training.venue = (

            update_data["venue"].strip()

            if update_data["venue"]

            else None

        )

    if "status" in update_data:

        status = (

            str(update_data["status"])

            .strip()

            .upper()

        )

        if status not in VALID_STATUSES:

            raise HTTPException(

                status_code=400,

                detail="Invalid training status.",

            )

        training.status = status

    if "is_department_wise" in update_data:

        training.is_department_wise = (

            update_data["is_department_wise"]

        )

    if "attendance_required" in update_data:

        training.attendance_required = (

            update_data["attendance_required"]

        )

    if "ojt_required" in update_data:

        training.ojt_required = (

            update_data["ojt_required"]

        )

    if "trainer_name" in update_data:

        training.trainer_name = (

            update_data["trainer_name"].strip()

            if update_data["trainer_name"]

            else None

        )

    if (

        training.training_to_date

        and training.scheduled_date

        and training.training_to_date

        < training.scheduled_date

    ):

        raise HTTPException(

            status_code=400,

            detail=(

                "Training end date cannot be "

                "before the start date."

            ),

        )

    training.updated_at = datetime.utcnow()

    await db.commit()

    await db.refresh(training)

    return {

        "success": True,

        "message": "Training updated successfully.",

        "training_id": training.id,

    }

# ============================================================

# RESCHEDULE TRAINING

# ============================================================

@router.patch("/{training_id}/reschedule")

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

    if training is None:

        raise HTTPException(

            status_code=404,

            detail="Training not found.",

        )

    if training.original_date is None:

        training.original_date = (

            training.scheduled_date

        )

    training.rescheduled_date = data.new_date

    training.scheduled_date = data.new_date

    if data.new_time is not None:

        training.scheduled_time = data.new_time

    training.reschedule_reason = (

        data.reason.strip()

    )

    training.status = "RESCHEDULED"

    training.updated_at = datetime.utcnow()

    await db.commit()

    await db.refresh(training)

    return {

        "success": True,

        "message": "Training rescheduled successfully.",

        "training_id": training.id,

        "scheduled_date": training.scheduled_date,

        "scheduled_time": training.scheduled_time,

        "status": training.status,

    }

# ============================================================

# UPDATE STATUS

# ============================================================

@router.patch("/{training_id}/status")

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

    if training is None:

        raise HTTPException(

            status_code=404,

            detail="Training not found.",

        )

    status = (

        data.status.strip().upper()

    )

    if status not in VALID_STATUSES:

        raise HTTPException(

            status_code=400,

            detail="Invalid training status.",

        )

    training.status = status

    if status == "NOT_CONDUCTED":

        if not data.reason or not data.reason.strip():

            raise HTTPException(

                status_code=400,

                detail=(

                    "A reason is required when "

                    "training is not conducted."

                ),

            )

        training.not_conducted_reason = (

            data.reason.strip()

        )

    else:

        training.not_conducted_reason = None

    training.updated_at = datetime.utcnow()

    await db.commit()

    await db.refresh(training)

    return {

        "success": True,

        "message": "Training status updated successfully.",

        "training_id": training.id,

        "status": training.status,

        "reason": training.not_conducted_reason,

    }
