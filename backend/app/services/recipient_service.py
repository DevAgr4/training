from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hod import HOD
from app.models.line_manager import LineManager


class RecipientResolutionError(Exception):
    pass


def resolve_recipient(
    db: Session,
    recipient_type: str,
    recipient_id: int | None,
) -> dict:
    recipient_type = recipient_type.strip().upper()

    if recipient_id is None:
        raise RecipientResolutionError(
            f"recipient_id is required for {recipient_type}"
        )

    if recipient_type == "HOD":
        recipient = db.execute(
            select(HOD).where(HOD.id == recipient_id)
        ).scalar_one_or_none()

    elif recipient_type == "LINE_MANAGER":
        recipient = db.execute(
            select(LineManager).where(LineManager.id == recipient_id)
        ).scalar_one_or_none()

    else:
        raise RecipientResolutionError(
            f"Unsupported recipient type: {recipient_type}"
        )

    if not recipient:
        raise RecipientResolutionError(
            f"{recipient_type} with ID {recipient_id} was not found"
        )

    return {
        "id": recipient.id,
        "recipient_type": recipient_type,
        "name": recipient.name,
        "email": recipient.email,
        "whatsapp_number": recipient.whatsapp_number,
        "department_id": recipient.department_id,
    }