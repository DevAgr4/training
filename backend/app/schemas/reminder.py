from datetime import datetime, time
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ENUMS
# ============================================================

class ReminderType(str, Enum):
    MONTHLY = "MONTHLY"
    WEEKLY = "WEEKLY"
    BEFORE_TRAINING = "BEFORE_TRAINING"
    POST_TRAINING = "POST_TRAINING"
    DOCUMENT_SUBMISSION = "DOCUMENT_SUBMISSION"
    TRAINING_PERCENTAGE = "TRAINING_PERCENTAGE"


class RecipientType(str, Enum):
    HOD = "HOD"
    LINE_MANAGER = "LINE_MANAGER"
    HIGHER_UP = "HIGHER_UP"
    HR = "HR"


class ChannelType(str, Enum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


# ============================================================
# REMINDER CONFIGURATION
# ============================================================

class ReminderConfigCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    reminder_type: ReminderType

    days_before: int | None = Field(
        default=None,
        ge=0,
        le=365,
    )

    send_time: time | None = None

    enabled: bool = True


class ReminderConfigUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    reminder_type: ReminderType | None = None

    days_before: int | None = Field(
        default=None,
        ge=0,
        le=365,
    )

    send_time: time | None = None

    enabled: bool | None = None


class ReminderConfigResponse(BaseModel):
    id: int
    name: str
    reminder_type: ReminderType
    days_before: int | None
    send_time: time | None
    enabled: bool

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# REMINDER RECIPIENTS
# ============================================================

class ReminderRecipientCreate(BaseModel):
    recipient_type: RecipientType

    recipient_id: int | None = None

    channel: ChannelType


class ReminderRecipientResponse(BaseModel):
    id: int
    reminder_config_id: int
    recipient_type: RecipientType
    recipient_id: int | None
    channel: ChannelType

    model_config = ConfigDict(
        from_attributes=True
    )
class ReminderResponse(BaseModel):
    id: int
    training_id: int
    reminder_type: str
    recipient_type: str
    recipient_id: int | None
    channel: str
    scheduled_at: datetime
    status: str
    sent_at: datetime | None
    failure_reason: str | None

    model_config = ConfigDict(
        from_attributes=True
    )