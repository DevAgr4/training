from datetime import date, time
from pydantic import BaseModel, ConfigDict


# ============================================================
# TRAINING BASE
# ============================================================

class TrainingBase(BaseModel):
    training_name: str
    training_type: str | None = None

    department_id: int | None = None
    audience_id: int | None = None

    scheduled_date: date
    training_to_date: date | None = None
    scheduled_time: time | None = None

    duration_hours: float | None = None
    venue: str | None = None

    is_department_wise: bool = False
    attendance_required: bool = True
    ojt_required: bool = False

    trainer_name: str | None = None


# ============================================================
# CREATE
# ============================================================

class TrainingCreate(TrainingBase):
    pass


# ============================================================
# UPDATE
# ============================================================

class TrainingUpdate(BaseModel):
    training_name: str | None = None
    training_type: str | None = None

    department_id: int | None = None
    audience_id: int | None = None

    scheduled_date: date | None = None
    training_to_date: date | None = None
    scheduled_time: time | None = None

    duration_hours: float | None = None
    venue: str | None = None

    status: str | None = None

    is_department_wise: bool | None = None
    attendance_required: bool | None = None
    ojt_required: bool | None = None

    trainer_name: str | None = None


# ============================================================
# RESCHEDULE
# ============================================================

class TrainingReschedule(BaseModel):
    new_date: date
    new_time: time | None = None
    reason: str


# ============================================================
# STATUS UPDATE
# ============================================================

class TrainingStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


# ============================================================
# RESPONSE
# ============================================================

class TrainingResponse(TrainingBase):
    id: int
    status: str

    original_date: date | None = None
    rescheduled_date: date | None = None

    reschedule_reason: str | None = None
    not_conducted_reason: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )