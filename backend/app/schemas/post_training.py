from datetime import date

from pydantic import BaseModel


class PostTrainingResponse(BaseModel):
    training_id: int
    training_name: str
    scheduled_date: date
    status: str

    attendance_required: bool
    ojt_required: bool

    attendance_status: str | None = None
    ojt_status: str | None = None


class TrainingConductedRequest(BaseModel):
    conducted: bool
    reason: str | None = None


class DocumentStatusUpdate(BaseModel):
    status: str
    received_via: str | None = None
    remarks: str | None = None