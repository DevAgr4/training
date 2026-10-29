from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db


router = APIRouter(
    prefix="/api/departments",
    tags=["Departments"]
)


@router.get("")
async def get_departments(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("""
            SELECT
                id,
                name
            FROM departments
            ORDER BY name
        """)
    )

    departments = result.mappings().all()

    return {
        "value": [
            {
                "id": department["id"],
                "name": department["name"],
            }
            for department in departments
        ],
        "Count": len(departments),
    }