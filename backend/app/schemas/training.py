from datetime import date, time
from pydantic import BaseModel, ConfigDict


class TrainingBase(BaseModel):
    training_name: str
    training_type: str | None = None
    department_id: int
    scheduled_date: date
    scheduled_time: time | None = None
    is_department_wise: bool = False
    attendance_required: bool = True
    ojt_required: bool = False
    trainer_name: str | None = None


class TrainingCreate(TrainingBase):
    pass


class TrainingUpdate(BaseModel):
    training_name: str | None = None
    training_type: str | None = None
    department_id: int | None = None
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    status: str | None = None
    is_department_wise: bool | None = None
    attendance_required: bool | None = None
    ojt_required: bool | None = None
    trainer_name: str | None = None


class TrainingReschedule(BaseModel):
    new_date: date
    reason: str


class TrainingStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


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