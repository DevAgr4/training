from fastapi import APIRouter, HTTPException

from app.database.connection import AsyncSessionLocal
from app.services.recipient_service import (
    RecipientResolutionError,
    resolve_recipient,
)

router = APIRouter(
    prefix="/api/recipient-test",
    tags=["Recipient Test"],
)


@router.get("/{recipient_type}/{recipient_id}")
async def test_recipient(
    recipient_type: str,
    recipient_id: int,
):
    async with AsyncSessionLocal() as db:
        try:
            # The resolver currently uses synchronous Session.
            # This endpoint is only a temporary development check.
            raise HTTPException(
                status_code=501,
                detail="Use the Celery sync resolver test instead.",
            )

        except RecipientResolutionError as exc:
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            )