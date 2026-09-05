from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.hod import HOD
from app.models.line_manager import LineManager
from app.models.training import Training
from app.models.training_assignment import TrainingAssignment


router = APIRouter(
    prefix="/api/excel",
    tags=["Excel Import"]
)


# --------------------------------------------------
# Required Excel columns
# --------------------------------------------------

REQUIRED_COLUMNS = [
    "Employee",
    "Employee Email",
    "Training",
    "Training Date",
    "Department",
    "HOD",
    "HOD Email",
    "Line Manager",
    "Manager Email",
]


# ==================================================
# HELPER FUNCTIONS
# ==================================================

async def get_or_create_department(
    db: AsyncSession,
    name: str,
) -> Department:

    result = await db.execute(
        select(Department).where(
            Department.name == name
        )
    )

    department = result.scalar_one_or_none()

    if department:
        return department

    department = Department(
        name=name
    )

    db.add(department)

    await db.flush()

    return department


async def get_or_create_hod(
    db: AsyncSession,
    name: str,
    email: str,
    department_id: int,
) -> HOD:

    result = await db.execute(
        select(HOD).where(
            HOD.email == email,
            HOD.department_id == department_id,
        )
    )

    hod = result.scalar_one_or_none()

    if hod:
        hod.name = name
        return hod

    hod = HOD(
        name=name,
        email=email,
        department_id=department_id,
    )

    db.add(hod)

    await db.flush()

    return hod


async def get_or_create_line_manager(
    db: AsyncSession,
    name: str,
    email: str,
    department_id: int,
) -> LineManager:

    result = await db.execute(
        select(LineManager).where(
            LineManager.email == email,
            LineManager.department_id == department_id,
        )
    )

    manager = result.scalar_one_or_none()

    if manager:
        manager.name = name
        return manager

    manager = LineManager(
        name=name,
        email=email,
        department_id=department_id,
    )

    db.add(manager)

    await db.flush()

    return manager


# ==================================================
# EXCEL VALIDATION
# ==================================================

def validate_dataframe(dataframe: pd.DataFrame):

    errors = []

    # --------------------------------------------------
    # Clean column names
    # --------------------------------------------------

    dataframe.columns = [
        str(column).strip()
        for column in dataframe.columns
    ]

    # --------------------------------------------------
    # Check required columns
    # --------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        return {
            "valid": False,
            "missing_columns": missing_columns,
            "errors": [],
        }

    # --------------------------------------------------
    # Remove empty rows
    # --------------------------------------------------

    dataframe = dataframe.dropna(
        how="all"
    ).copy()

    # --------------------------------------------------
    # Employee validation
    # --------------------------------------------------

    if dataframe["Employee"].isna().any():

        rows = dataframe.index[
            dataframe["Employee"].isna()
        ].tolist()

        errors.append({
            "field": "Employee",
            "rows": [row + 2 for row in rows],
            "message": "Employee name is missing.",
        })

    # --------------------------------------------------
    # Training validation
    # --------------------------------------------------

    if dataframe["Training"].isna().any():

        rows = dataframe.index[
            dataframe["Training"].isna()
        ].tolist()

        errors.append({
            "field": "Training",
            "rows": [row + 2 for row in rows],
            "message": "Training name is missing.",
        })

    # --------------------------------------------------
    # Department validation
    # --------------------------------------------------

    if dataframe["Department"].isna().any():

        rows = dataframe.index[
            dataframe["Department"].isna()
        ].tolist()

        errors.append({
            "field": "Department",
            "rows": [row + 2 for row in rows],
            "message": "Department is missing.",
        })

    # --------------------------------------------------
    # HOD validation
    # --------------------------------------------------

    if dataframe["HOD"].isna().any():

        rows = dataframe.index[
            dataframe["HOD"].isna()
        ].tolist()

        errors.append({
            "field": "HOD",
            "rows": [row + 2 for row in rows],
            "message": "HOD name is missing.",
        })

    # --------------------------------------------------
    # HOD email validation
    # --------------------------------------------------

    if dataframe["HOD Email"].isna().any():

        rows = dataframe.index[
            dataframe["HOD Email"].isna()
        ].tolist()

        errors.append({
            "field": "HOD Email",
            "rows": [row + 2 for row in rows],
            "message": "HOD email is missing.",
        })

    # --------------------------------------------------
    # Line Manager validation
    # --------------------------------------------------

    if dataframe["Line Manager"].isna().any():

        rows = dataframe.index[
            dataframe["Line Manager"].isna()
        ].tolist()

        errors.append({
            "field": "Line Manager",
            "rows": [row + 2 for row in rows],
            "message": "Line Manager name is missing.",
        })

    # --------------------------------------------------
    # Training date validation
    # --------------------------------------------------

    parsed_dates = pd.to_datetime(
        dataframe["Training Date"],
        errors="coerce"
    )

    invalid_dates = parsed_dates.isna()

    if invalid_dates.any():

        rows = dataframe.index[
            invalid_dates
        ].tolist()

        errors.append({
            "field": "Training Date",
            "rows": [row + 2 for row in rows],
            "message": "Training date is invalid or missing.",
        })

    # --------------------------------------------------
    # Duplicate validation
    # --------------------------------------------------

    duplicates = dataframe.duplicated(
        subset=[
            "Employee",
            "Training",
            "Training Date",
        ],
        keep=False,
    )

    duplicate_rows = dataframe.index[
        duplicates
    ].tolist()

    if duplicate_rows:

        errors.append({
            "field": "Duplicate Training",
            "rows": [row + 2 for row in duplicate_rows],
            "message": (
                "Duplicate employee/training/date "
                "combination found."
            ),
        })

    return {
        "valid": len(errors) == 0,
        "missing_columns": [],
        "errors": errors,
        "dataframe": dataframe,
    }


# ==================================================
# 1. UPLOAD + PREVIEW
# ==================================================

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...)
):
    """
    Upload and validate an Excel file.

    This endpoint does NOT save data to PostgreSQL.
    It validates the spreadsheet and returns a preview.
    """

    # --------------------------------------------------
    # Check file name
    # --------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was selected."
        )

    filename = file.filename.lower()

    if not filename.endswith(
        (".xlsx", ".xls")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files "
                "(.xlsx or .xls) are allowed."
            )
        )

    # --------------------------------------------------
    # Read file
    # --------------------------------------------------

    file_content = await file.read()

    if not file_content:

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    try:

        dataframe = pd.read_excel(
            BytesIO(file_content)
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unable to read Excel file: {str(error)}"
            )
        )

    # --------------------------------------------------
    # Validate
    # --------------------------------------------------

    validation = validate_dataframe(
        dataframe
    )

    if validation["missing_columns"]:

        return {
            "success": False,
            "message": "Excel validation failed.",
            "missing_columns": (
                validation["missing_columns"]
            ),
            "available_columns": list(
                dataframe.columns
            ),
        }

    if validation["errors"]:

        return {
            "success": False,
            "message": (
                "Excel contains validation errors."
            ),
            "total_rows": len(
                validation["dataframe"]
            ),
            "errors": validation["errors"],
        }

    dataframe = validation["dataframe"]

    # --------------------------------------------------
    # Create preview
    # --------------------------------------------------

    preview_dataframe = dataframe.head(10).copy()

    preview_dataframe["Training Date"] = (
        pd.to_datetime(
            preview_dataframe["Training Date"]
        ).dt.strftime("%Y-%m-%d")
    )

    preview = (
        preview_dataframe
        .fillna("")
        .to_dict(orient="records")
    )

    return {
        "success": True,
        "message": (
            "Excel file validated successfully."
        ),
        "filename": file.filename,
        "total_rows": len(dataframe),
        "preview_rows": len(preview),
        "preview": preview,
    }


# ==================================================
# 2. IMPORT EXCEL → POSTGRESQL
# ==================================================

@router.post("/import")
async def import_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate Excel and import its data into PostgreSQL.

    Creates/updates:

    - Departments
    - HODs
    - Line Managers
    - Employees
    - Trainings
    - Training Assignments
    """

    # --------------------------------------------------
    # Check file
    # --------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was selected."
        )

    filename = file.filename.lower()

    if not filename.endswith(
        (".xlsx", ".xls")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files "
                "(.xlsx or .xls) are allowed."
            )
        )

    file_content = await file.read()

    if not file_content:

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    # --------------------------------------------------
    # Read Excel
    # --------------------------------------------------

    try:

        dataframe = pd.read_excel(
            BytesIO(file_content)
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unable to read Excel file: {str(error)}"
            )
        )

    # --------------------------------------------------
    # Validate Excel
    # --------------------------------------------------

    validation = validate_dataframe(
        dataframe
    )

    if validation["missing_columns"]:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Excel validation failed.",
                "missing_columns": (
                    validation["missing_columns"]
                ),
            },
        )

    if validation["errors"]:

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Excel contains validation errors."
                ),
                "errors": validation["errors"],
            },
        )

    dataframe = validation["dataframe"]

    # --------------------------------------------------
    # Counters
    # --------------------------------------------------

    imported_rows = 0
    created_departments = 0
    created_hods = 0
    created_managers = 0
    created_employees = 0
    created_trainings = 0
    created_assignments = 0

    try:

        # ==================================================
        # Process every Excel row
        # ==================================================

        for index, row in dataframe.iterrows():

            # --------------------------------------------------
            # Read values
            # --------------------------------------------------

            employee_name = str(
                row["Employee"]
            ).strip()

            employee_email = (
                str(row["Employee Email"]).strip()
                if pd.notna(
                    row["Employee Email"]
                )
                else None
            )

            training_name = str(
                row["Training"]
            ).strip()

            training_date = pd.to_datetime(
                row["Training Date"]
            ).date()

            department_name = str(
                row["Department"]
            ).strip()

            hod_name = str(
                row["HOD"]
            ).strip()

            hod_email = str(
                row["HOD Email"]
            ).strip()

            manager_name = str(
                row["Line Manager"]
            ).strip()

            manager_email = str(
                row["Manager Email"]
            ).strip()

            # ==================================================
            # Department
            # ==================================================

            department_result = await db.execute(
                select(Department).where(
                    Department.name
                    == department_name
                )
            )

            department = (
                department_result
                .scalar_one_or_none()
            )

            if not department:

                department = Department(
                    name=department_name
                )

                db.add(department)

                await db.flush()

                created_departments += 1

            # ==================================================
            # HOD
            # ==================================================

            hod_result = await db.execute(
                select(HOD).where(
                    HOD.email == hod_email,
                    HOD.department_id
                    == department.id,
                )
            )

            hod = (
                hod_result
                .scalar_one_or_none()
            )

            if hod:

                hod.name = hod_name

            else:

                hod = HOD(
                    name=hod_name,
                    email=hod_email,
                    department_id=department.id,
                )

                db.add(hod)

                await db.flush()

                created_hods += 1

            # ==================================================
            # Line Manager
            # ==================================================

            manager_result = await db.execute(
                select(LineManager).where(
                    LineManager.email
                    == manager_email,
                    LineManager.department_id
                    == department.id,
                )
            )

            manager = (
                manager_result
                .scalar_one_or_none()
            )

            if manager:

                manager.name = manager_name

            else:

                manager = LineManager(
                    name=manager_name,
                    email=manager_email,
                    department_id=department.id,
                )

                db.add(manager)

                await db.flush()

                created_managers += 1

            # ==================================================
            # Employee
            # ==================================================

            employee_result = await db.execute(
                select(Employee).where(
                    Employee.name
                    == employee_name,
                    Employee.department_id
                    == department.id,
                )
            )

            employee = (
                employee_result
                .scalar_one_or_none()
            )

            if employee:

                employee.email = employee_email
                employee.hod_id = hod.id
                employee.line_manager_id = manager.id

            else:

                # Temporary employee code because
                # current Excel template has no
                # employee code column.

                employee_code = (
                    f"EXCEL-{index + 2}"
                )

                employee = Employee(
                    employee_code=employee_code,
                    name=employee_name,
                    email=employee_email,
                    department_id=department.id,
                    hod_id=hod.id,
                    line_manager_id=manager.id,
                )

                db.add(employee)

                await db.flush()

                created_employees += 1

            # ==================================================
            # Training
            # ==================================================

            training_result = await db.execute(
                select(Training).where(
                    Training.training_name
                    == training_name,
                    Training.department_id
                    == department.id,
                    Training.scheduled_date
                    == training_date,
                )
            )

            training = (
                training_result
                .scalar_one_or_none()
            )

            if not training:

                training = Training(
                    training_name=training_name,
                    department_id=department.id,
                    scheduled_date=training_date,
                    status="SCHEDULED",
                )

                db.add(training)

                await db.flush()

                created_trainings += 1

            # ==================================================
            # Training Assignment
            # ==================================================

            assignment_result = await db.execute(
                select(
                    TrainingAssignment
                ).where(
                    TrainingAssignment.training_id
                    == training.id,
                    TrainingAssignment.employee_id
                    == employee.id,
                )
            )

            assignment = (
                assignment_result
                .scalar_one_or_none()
            )

            if not assignment:

                assignment = TrainingAssignment(
                    training_id=training.id,
                    employee_id=employee.id,
                    status="ASSIGNED",
                )

                db.add(assignment)

                created_assignments += 1

            imported_rows += 1

        # --------------------------------------------------
        # Commit transaction
        # --------------------------------------------------

        await db.commit()

    except Exception as error:

        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Excel import failed: {str(error)}"
            ),
        )

    # ==================================================
    # Return result
    # ==================================================

    return {
        "success": True,
        "message": (
            "Excel data imported successfully."
        ),
        "filename": file.filename,
        "imported_rows": imported_rows,
        "created_departments": created_departments,
        "created_hods": created_hods,
        "created_line_managers": created_managers,
        "created_employees": created_employees,
        "created_trainings": created_trainings,
        "created_assignments": created_assignments,
    }