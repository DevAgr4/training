from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.employee import Employee
from app.models.hod import HOD
from app.models.line_manager import LineManager
from app.models.training import Training
from app.models.training_assignment import TrainingAssignment


async def get_or_create_department(
    db: AsyncSession,
    name: str,
) -> Department:

    result = await db.execute(
        select(Department).where(Department.name == name)
    )

    department = result.scalar_one_or_none()

    if department:
        return department

    department = Department(name=name)
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


async def get_or_create_employee(
    db: AsyncSession,
    name: str,
    email: str | None,
    employee_code: str,
    department_id: int,
    hod_id: int,
    line_manager_id: int,
) -> Employee:

    result = await db.execute(
        select(Employee).where(
            Employee.employee_code == employee_code
        )
    )

    employee = result.scalar_one_or_none()

    if employee:
        employee.name = name
        employee.email = email
        employee.department_id = department_id
        employee.hod_id = hod_id
        employee.line_manager_id = line_manager_id

        return employee

    employee = Employee(
        employee_code=employee_code,
        name=name,
        email=email,
        department_id=department_id,
        hod_id=hod_id,
        line_manager_id=line_manager_id,
    )

    db.add(employee)

    await db.flush()

    return employee


async def create_training(
    db: AsyncSession,
    training_name: str,
    department_id: int,
    training_date,
) -> Training:

    result = await db.execute(
        select(Training).where(
            Training.training_name == training_name,
            Training.department_id == department_id,
            Training.scheduled_date == training_date,
        )
    )

    training = result.scalar_one_or_none()

    if training:
        return training

    training = Training(
        training_name=training_name,
        department_id=department_id,
        scheduled_date=training_date,
        status="SCHEDULED",
    )

    db.add(training)

    await db.flush()

    return training


async def import_training_excel(
    db: AsyncSession,
    dataframe: pd.DataFrame,
):

    imported_rows = 0
    created_trainings = 0
    created_employees = 0
    created_assignments = 0

    for index, row in dataframe.iterrows():

        employee_name = str(row["Employee"]).strip()

        employee_email = (
            str(row["Employee Email"]).strip()
            if pd.notna(row["Employee Email"])
            else None
        )

        training_name = str(row["Training"]).strip()

        training_date = pd.to_datetime(
            row["Training Date"]
        ).date()

        department_name = str(row["Department"]).strip()

        hod_name = str(row["HOD"]).strip()

        hod_email = str(row["HOD Email"]).strip()

        manager_name = str(row["Line Manager"]).strip()

        manager_email = str(row["Manager Email"]).strip()

        # --------------------------------------------------
        # Department
        # --------------------------------------------------

        department = await get_or_create_department(
            db,
            department_name,
        )

        # --------------------------------------------------
        # HOD
        # --------------------------------------------------

        hod = await get_or_create_hod(
            db,
            hod_name,
            hod_email,
            department.id,
        )

        # --------------------------------------------------
        # Line Manager
        # --------------------------------------------------

        manager = await get_or_create_line_manager(
            db,
            manager_name,
            manager_email,
            department.id,
        )

        # --------------------------------------------------
        # Employee
        # --------------------------------------------------

        employee_code = f"EXCEL-{index + 2}"

        employee_result = await db.execute(
            select(Employee).where(
                Employee.name == employee_name,
                Employee.department_id == department.id,
            )
        )

        existing_employee = employee_result.scalar_one_or_none()

        if existing_employee:

            employee = existing_employee

            employee.email = employee_email
            employee.hod_id = hod.id
            employee.line_manager_id = manager.id

        else:

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

        # --------------------------------------------------
        # Training
        # --------------------------------------------------

        training_result = await db.execute(
            select(Training).where(
                Training.training_name == training_name,
                Training.department_id == department.id,
                Training.scheduled_date == training_date,
            )
        )

        training = training_result.scalar_one_or_none()

        if training:

            pass

        else:

            training = Training(
                training_name=training_name,
                department_id=department.id,
                scheduled_date=training_date,
                status="SCHEDULED",
            )

            db.add(training)

            await db.flush()

            created_trainings += 1

        # --------------------------------------------------
        # Training Assignment
        # --------------------------------------------------

        assignment_result = await db.execute(
            select(TrainingAssignment).where(
                TrainingAssignment.training_id == training.id,
                TrainingAssignment.employee_id == employee.id,
            )
        )

        assignment = assignment_result.scalar_one_or_none()

        if not assignment:

            assignment = TrainingAssignment(
                training_id=training.id,
                employee_id=employee.id,
                status="ASSIGNED",
            )

            db.add(assignment)

            created_assignments += 1

        imported_rows += 1

    await db.commit()

    return {
        "imported_rows": imported_rows,
        "created_employees": created_employees,
        "created_trainings": created_trainings,
        "created_assignments": created_assignments,
    }