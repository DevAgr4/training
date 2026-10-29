from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


# ============================================================
# DEPARTMENT-WISE REPORT
# ============================================================

@router.get("/department-wise")
async def get_department_wise_report(
    db: AsyncSession = Depends(get_db),
):
    # ========================================================
    # GET DEPARTMENT-WISE DATA
    #
    # Includes:
    # 1. Trainings assigned to a department
    # 2. Trainings with department_id = NULL
    #    -> shown as "Unassigned / All Departments"
    # ========================================================

    query = text(
        """
        SELECT
            d.id AS department_id,
            d.name AS department_name,

            COUNT(t.id) AS total_trainings,

            COUNT(
                CASE
                    WHEN t.status = 'COMPLETED'
                    THEN 1
                END
            ) AS completed_trainings,

            COUNT(
                CASE
                    WHEN t.status IN (
                        'PENDING',
                        'SCHEDULED',
                        'RESCHEDULED'
                    )
                    THEN 1
                END
            ) AS pending_trainings,

            COUNT(
                CASE
                    WHEN t.status = 'NOT_CONDUCTED'
                    THEN 1
                END
            ) AS not_conducted_trainings,

            COUNT(
                CASE
                    WHEN t.status = 'RESCHEDULED'
                    THEN 1
                END
            ) AS rescheduled_trainings

        FROM departments d

        LEFT JOIN trainings t
            ON t.department_id = d.id

        GROUP BY
            d.id,
            d.name

        ORDER BY
            d.name
        """
    )

    result = await db.execute(query)

    rows = result.mappings().all()

    reports = []

    # ========================================================
    # NORMAL DEPARTMENT REPORTS
    # ========================================================

    for row in rows:

        total = int(
            row["total_trainings"] or 0
        )

        completed = int(
            row["completed_trainings"] or 0
        )

        pending = int(
            row["pending_trainings"] or 0
        )

        not_conducted = int(
            row["not_conducted_trainings"] or 0
        )

        rescheduled = int(
            row["rescheduled_trainings"] or 0
        )

        percentage = (
            round(
                (completed / total) * 100,
                2,
            )
            if total > 0
            else 0
        )

        reports.append(
            {
                "department_id":
                    row["department_id"],

                "department_name":
                    row["department_name"],

                "total_trainings":
                    total,

                "completed_trainings":
                    completed,

                "pending_trainings":
                    pending,

                "not_conducted_trainings":
                    not_conducted,

                "rescheduled_trainings":
                    rescheduled,

                "completion_percentage":
                    percentage,
            }
        )

    # ========================================================
    # TRAININGS WITHOUT A DEPARTMENT
    #
    # Your imported trainings currently have:
    #
    # department_id = NULL
    #
    # These were previously excluded from the report.
    # We explicitly include them here.
    # ========================================================

    unassigned_query = text(
        """
        SELECT
            COUNT(t.id) AS total_trainings,

            COUNT(
                CASE
                    WHEN t.status = 'COMPLETED'
                    THEN 1
                END
            ) AS completed_trainings,

            COUNT(
                CASE
                    WHEN t.status IN (
                        'PENDING',
                        'SCHEDULED',
                        'RESCHEDULED'
                    )
                    THEN 1
                END
            ) AS pending_trainings,

            COUNT(
                CASE
                    WHEN t.status = 'NOT_CONDUCTED'
                    THEN 1
                END
            ) AS not_conducted_trainings,

            COUNT(
                CASE
                    WHEN t.status = 'RESCHEDULED'
                    THEN 1
                END
            ) AS rescheduled_trainings

        FROM trainings t

        WHERE t.department_id IS NULL
        """
    )

    unassigned_result = await db.execute(
        unassigned_query
    )

    unassigned = (
        unassigned_result
        .mappings()
        .first()
    )

    if unassigned:

        total = int(
            unassigned["total_trainings"] or 0
        )

        completed = int(
            unassigned["completed_trainings"] or 0
        )

        pending = int(
            unassigned["pending_trainings"] or 0
        )

        not_conducted = int(
            unassigned["not_conducted_trainings"] or 0
        )

        rescheduled = int(
            unassigned["rescheduled_trainings"] or 0
        )

        # Only add the row when there are actually
        # trainings without a department.
        if total > 0:

            percentage = (
                round(
                    (completed / total) * 100,
                    2,
                )
                if total > 0
                else 0
            )

            reports.append(
                {
                    "department_id": None,

                    "department_name":
                        "Unassigned / All Departments",

                    "total_trainings":
                        total,

                    "completed_trainings":
                        completed,

                    "pending_trainings":
                        pending,

                    "not_conducted_trainings":
                        not_conducted,

                    "rescheduled_trainings":
                        rescheduled,

                    "completion_percentage":
                        percentage,
                }
            )

    # ========================================================
    # CONSOLIDATED TOTALS
    # ========================================================

    total_trainings = sum(
        item["total_trainings"]
        for item in reports
    )

    completed_trainings = sum(
        item["completed_trainings"]
        for item in reports
    )

    pending_trainings = sum(
        item["pending_trainings"]
        for item in reports
    )

    not_conducted_trainings = sum(
        item["not_conducted_trainings"]
        for item in reports
    )

    rescheduled_trainings = sum(
        item["rescheduled_trainings"]
        for item in reports
    )

    overall_percentage = (
        round(
            (
                completed_trainings
                / total_trainings
            )
            * 100,
            2,
        )
        if total_trainings > 0
        else 0
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "value": reports,

        "Count": len(reports),

        "summary": {
            "total_trainings":
                total_trainings,

            "completed_trainings":
                completed_trainings,

            "pending_trainings":
                pending_trainings,

            "not_conducted_trainings":
                not_conducted_trainings,

            "rescheduled_trainings":
                rescheduled_trainings,

            "completion_percentage":
                overall_percentage,
        },
    }