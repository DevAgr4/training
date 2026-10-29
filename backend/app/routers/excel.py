from io import BytesIO
from datetime import datetime, date, time, timedelta
import re

import httpx
import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.target_audience import TargetAudience
from app.models.training import Training


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/excel",
    tags=["Excel Import"],
)


# ============================================================
# TRAINING CALENDAR FORMAT
# ============================================================

REQUIRED_COLUMNS = [
    "S.No",
    "Training From Date",
    "Training To Date",
    "Day",
    "Training Topic",
    "Training Type",
    "Target Audience",
    "Trainer's Name",
    "Timing",
    "Duration of the Training Hours",
    "Venue",
]


# The calendar should contain ONLY these columns.
ALLOWED_COLUMNS = REQUIRED_COLUMNS.copy()


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {
    # Serial number
    "S.No.": "S.No",
    "S No": "S.No",
    "S.No": "S.No",
    "Serial No": "S.No",
    "Serial Number": "S.No",

    # Dates
    "Training From Date": "Training From Date",
    "From Date": "Training From Date",
    "Training Start Date": "Training From Date",
    "Start Date": "Training From Date",

    "Training To Date": "Training To Date",
    "To Date": "Training To Date",
    "Training End Date": "Training To Date",
    "End Date": "Training To Date",

    # Training
    "Training Topic": "Training Topic",
    "Training Name": "Training Topic",
    "Training": "Training Topic",

    "Training Type": "Training Type",
    "Type": "Training Type",

    # Audience
    "Target Audience": "Target Audience",
    "Audience": "Target Audience",

    # Trainer
    "Trainer's Name": "Trainer's Name",
    "Trainer Name": "Trainer's Name",
    "Trainer": "Trainer's Name",

    # Timing
    "Timing": "Timing",
    "Training Time": "Timing",
    "Time": "Timing",

    # Duration
    "Duration of the Training Hours":
        "Duration of the Training Hours",
    "Duration":
        "Duration of the Training Hours",
    "Training Duration":
        "Duration of the Training Hours",

    # Venue
    "Venue": "Venue",
    "Training Venue": "Venue",
    "Location": "Venue",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_value(
    value,
    default=None,
):
    """
    Clean values coming from Excel.
    """

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return default

    return value


def normalize_columns(
    dataframe: pd.DataFrame,
):
    """
    Normalize Excel headers using known aliases.
    """

    dataframe = dataframe.copy()

    dataframe.columns = [
        str(column).strip()
        for column in dataframe.columns
    ]

    rename_map = {}

    for column in dataframe.columns:

        normalized = COLUMN_ALIASES.get(
            column
        )

        if (
            normalized
            and normalized != column
            and normalized not in dataframe.columns
        ):
            rename_map[column] = normalized

    if rename_map:
        dataframe = dataframe.rename(
            columns=rename_map
        )

    return dataframe


# ============================================================
# DATE PARSER
# ============================================================

def parse_excel_date(value):
    """
    Convert Excel date values into Python date.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    parsed = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed.date()


# ============================================================
# TIME PARSER
# ============================================================

def parse_training_time(
    value,
):
    """
    Parse the beginning of the training time.

    Supported examples:

        09:00 AM
        09:00
        9 AM
        09:00 AM - 01:00 PM
        09:00-13:00
        09:00 AM to 01:00 PM
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, datetime):
        return value.time()

    if isinstance(value, time):
        return value

    # Excel time-like object
    if hasattr(value, "hour") and hasattr(
        value,
        "minute",
    ):
        try:
            return time(
                int(value.hour),
                int(value.minute),
                int(
                    getattr(
                        value,
                        "second",
                        0,
                    )
                ),
            )
        except Exception:
            pass

    text = str(value).strip()

    if not text:
        return None

    # Normalize separators.
    text = re.sub(
        r"\s+to\s+",
        " - ",
        text,
        flags=re.IGNORECASE,
    )

    # Take the starting time from a range.
    if " - " in text:

        text = text.split(
            " - ",
            1,
        )[0].strip()

    elif "-" in text:

        parts = text.split(
            "-",
            1,
        )

        if len(parts) == 2:
            text = parts[0].strip()

    formats = [
        "%I:%M %p",
        "%I:%M%p",
        "%I %p",
        "%H:%M",
        "%H:%M:%S",
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                text,
                fmt,
            ).time()

        except ValueError:
            continue

    parsed = pd.to_datetime(
        text,
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed.time()


# ============================================================
# DURATION PARSER
# ============================================================

def parse_duration(
    value,
):
    """
    Parse duration in hours.

    Examples:

        2
        2.5
        "2"
        "2.5 hours"
        "4 Hours"
    """

    value = clean_value(
        value
    )

    if value is None:
        return None

    if isinstance(
        value,
        (int, float),
    ):

        if float(value) < 0:
            return None

        return float(value)

    text = str(value).strip()

    match = re.search(
        r"\d+(?:\.\d+)?",
        text,
    )

    if not match:
        return None

    try:

        duration = float(
            match.group()
        )

        if duration < 0:
            return None

        return duration

    except ValueError:
        return None


# ============================================================
# DAY VALIDATION
# ============================================================

VALID_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


def validate_day(
    value,
    training_date,
):
    """
    Validate the Day column against
    Training From Date.

    Empty Day is considered invalid because
    Day is part of the required calendar format.
    """

    value = clean_value(
        value
    )

    if value is None:
        return False

    if training_date is None:
        return False

    day = str(
        value
    ).strip().lower()

    if day not in VALID_DAYS:
        return False

    expected_day = (
        training_date
        .strftime("%A")
        .lower()
    )

    return day == expected_day


# ============================================================
# SERIAL NUMBER VALIDATION
# ============================================================

def parse_serial_number(
    value,
):
    """
    Parse S.No.
    """

    value = clean_value(
        value
    )

    if value is None:
        return None

    try:

        number = int(
            float(value)
        )

        if number <= 0:
            return None

        return number

    except (
        ValueError,
        TypeError,
    ):
        return None


# ============================================================
# DATAFRAME VALIDATION
# ============================================================

def validate_dataframe(
    dataframe: pd.DataFrame,
):
    """
    Validate the complete training calendar.
    """

    errors = []

    # --------------------------------------------------------
    # Normalize headers
    # --------------------------------------------------------

    dataframe = normalize_columns(
        dataframe
    )

    # --------------------------------------------------------
    # Remove completely empty rows
    # --------------------------------------------------------

    dataframe = dataframe.dropna(
        how="all"
    ).copy()

    if dataframe.empty:

        return {
            "valid": False,
            "missing_columns": [],
            "extra_columns": [],
            "available_columns": [],
            "errors": [
                {
                    "field": "Excel File",
                    "rows": [],
                    "message": (
                        "The Excel file does not "
                        "contain any training rows."
                    ),
                }
            ],
            "dataframe": dataframe,
        }

    # --------------------------------------------------------
    # Detect missing columns
    # --------------------------------------------------------

    actual_columns = list(
        dataframe.columns
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in actual_columns
    ]

    # --------------------------------------------------------
    # Detect extra columns
    # --------------------------------------------------------

    extra_columns = [
        column
        for column in actual_columns
        if column not in ALLOWED_COLUMNS
    ]

    if missing_columns:

        return {
            "valid": False,
            "missing_columns": missing_columns,
            "extra_columns": extra_columns,
            "available_columns": actual_columns,
            "errors": [],
            "dataframe": dataframe,
        }

    # --------------------------------------------------------
    # Extra columns
    # --------------------------------------------------------

    if extra_columns:

        return {
            "valid": False,
            "missing_columns": [],
            "extra_columns": extra_columns,
            "available_columns": actual_columns,
            "errors": [
                {
                    "field": "Extra Columns",
                    "rows": [],
                    "message": (
                        "The training calendar must "
                        "contain only the 11 approved "
                        "columns."
                    ),
                }
            ],
            "dataframe": dataframe,
        }

    # ========================================================
    # ROW VALIDATION
    # ========================================================

    serial_numbers = set()

    from_dates = {}
    to_dates = {}

    # --------------------------------------------------------
    # S.No
    # --------------------------------------------------------

    invalid_serial_rows = []
    duplicate_serial_rows = []

    for index, value in dataframe[
        "S.No"
    ].items():

        serial = parse_serial_number(
            value
        )

        if serial is None:

            invalid_serial_rows.append(
                index
            )

        else:

            if serial in serial_numbers:
                duplicate_serial_rows.append(
                    index
                )

            serial_numbers.add(
                serial
            )

    if invalid_serial_rows:

        errors.append(
            {
                "field": "S.No",
                "rows": [
                    index + 2
                    for index in invalid_serial_rows
                ],
                "message": (
                    "S.No must contain a "
                    "positive number."
                ),
            }
        )

    if duplicate_serial_rows:

        errors.append(
            {
                "field": "S.No",
                "rows": [
                    index + 2
                    for index in duplicate_serial_rows
                ],
                "message": (
                    "Duplicate S.No found."
                ),
            }
        )

    # --------------------------------------------------------
    # Training From Date
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Training From Date"
    ].items():

        parsed = parse_excel_date(
            value
        )

        if parsed is None:

            invalid_rows.append(
                index
            )

        else:

            from_dates[index] = parsed

    if invalid_rows:

        errors.append(
            {
                "field": "Training From Date",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Training From Date is "
                    "missing or invalid."
                ),
            }
        )

    # --------------------------------------------------------
    # Training To Date
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Training To Date"
    ].items():

        parsed = parse_excel_date(
            value
        )

        if parsed is None:

            invalid_rows.append(
                index
            )

        else:

            to_dates[index] = parsed

    if invalid_rows:

        errors.append(
            {
                "field": "Training To Date",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Training To Date is "
                    "missing or invalid."
                ),
            }
        )

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    invalid_range_rows = []

    for index in dataframe.index:

        from_date = from_dates.get(
            index
        )

        to_date = to_dates.get(
            index
        )

        if (
            from_date
            and to_date
            and to_date < from_date
        ):

            invalid_range_rows.append(
                index
            )

    if invalid_range_rows:

        errors.append(
            {
                "field": "Training Date Range",
                "rows": [
                    index + 2
                    for index in invalid_range_rows
                ],
                "message": (
                    "Training To Date cannot "
                    "be before Training From Date."
                ),
            }
        )

    # --------------------------------------------------------
    # Day
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Day"
    ].items():

        if not validate_day(
            value,
            from_dates.get(index),
        ):

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": "Day",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Day must match the "
                    "Training From Date."
                ),
            }
        )

    # --------------------------------------------------------
    # Training Topic
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Training Topic"
    ].items():

        if clean_value(
            value
        ) is None:

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": "Training Topic",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Training Topic is required."
                ),
            }
        )

    # --------------------------------------------------------
    # Training Type
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Training Type"
    ].items():

        if clean_value(
            value
        ) is None:

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": "Training Type",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Training Type is required."
                ),
            }
        )

    # --------------------------------------------------------
    # Target Audience
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Target Audience"
    ].items():

        if clean_value(
            value
        ) is None:

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": "Target Audience",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Target Audience is required."
                ),
            }
        )

    # --------------------------------------------------------
    # Trainer
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Trainer's Name"
    ].items():

        if clean_value(
            value
        ) is None:

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": "Trainer's Name",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Trainer's Name is required."
                ),
            }
        )

    # --------------------------------------------------------
    # Timing
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Timing"
    ].items():

        if parse_training_time(
            value
        ) is None:

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": "Timing",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Timing is invalid. "
                    "Example: 09:00 AM - 01:00 PM."
                ),
            }
        )

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Duration of the Training Hours"
    ].items():

        duration = parse_duration(
            value
        )

        if duration is None:

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": (
                    "Duration of the Training Hours"
                ),
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Duration must be a "
                    "valid number of hours."
                ),
            }
        )

    # --------------------------------------------------------
    # Venue
    # --------------------------------------------------------

    invalid_rows = []

    for index, value in dataframe[
        "Venue"
    ].items():

        if clean_value(
            value
        ) is None:

            invalid_rows.append(
                index
            )

    if invalid_rows:

        errors.append(
            {
                "field": "Venue",
                "rows": [
                    index + 2
                    for index in invalid_rows
                ],
                "message": (
                    "Venue is required."
                ),
            }
        )

    # ========================================================
    # DUPLICATE TRAINING SCHEDULES
    # ========================================================

    duplicate_mask = dataframe.duplicated(
        subset=[
            "Training From Date",
            "Training To Date",
            "Training Topic",
            "Target Audience",
            "Trainer's Name",
        ],
        keep=False,
    )

    duplicate_indices = dataframe.index[
        duplicate_mask
    ].tolist()

    if duplicate_indices:

        errors.append(
            {
                "field": "Duplicate Training",
                "rows": [
                    index + 2
                    for index in duplicate_indices
                ],
                "message": (
                    "Duplicate training schedule "
                    "found for the same date, topic, "
                    "audience and trainer."
                ),
            }
        )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "valid": len(errors) == 0,
        "missing_columns": [],
        "extra_columns": [],
        "available_columns": actual_columns,
        "errors": errors,
        "dataframe": dataframe,
    }


# ============================================================
# RESOLVE TARGET AUDIENCE
# ============================================================

async def resolve_target_audience(
    db: AsyncSession,
    target_audience: str,
):
    """
    Resolve Target Audience from the master table.

    Target Audience records are maintained through the
    Settings / Master Recipient Excel. The training calendar
    must reference an existing Target Audience so that a typo
    cannot silently create an audience with no recipients.
    """

    target_audience = str(target_audience).strip()

    if not target_audience:
        return None

    result = await db.execute(
        select(TargetAudience).where(
            func.lower(TargetAudience.name)
            == target_audience.lower()
        )
    )

    return result.scalar_one_or_none()


# ============================================================
# REMINDER GENERATION
# ============================================================

async def generate_reminders_for_training(
    training_id: int,
):
    """
    Ask the reminder engine to generate
    reminders for a training.

    Recipient resolution is handled by
    reminder_engine.py using training.audience_id.
    """

    url = (
        "http://127.0.0.1:8000"
        f"/api/reminder-engine/training/"
        f"{training_id}/generate"
    )

    try:

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.post(
                url
            )

        # ----------------------------------------------------
        # HTTP error
        # ----------------------------------------------------

        if response.status_code >= 400:

            return {
                "success": False,
                "training_id": training_id,
                "reminders_created": 0,
                "error": (
                    "Reminder engine returned "
                    f"HTTP {response.status_code}: "
                    f"{response.text}"
                ),
            }

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception:

            return {
                "success": False,
                "training_id": training_id,
                "reminders_created": 0,
                "error": (
                    "Reminder engine returned "
                    "an invalid JSON response."
                ),
            }

        return {
            "success": bool(
                data.get(
                    "success",
                    True,
                )
            ),
            "training_id": training_id,
            "reminders_created": int(
                data.get(
                    "reminders_created",
                    0,
                )
            ),
            "error": data.get(
                "error"
            ),
        }

    except Exception as error:

        return {
            "success": False,
            "training_id": training_id,
            "reminders_created": 0,
            "error": str(error),
        }


# ============================================================
# PREVIEW DATA
# ============================================================

def build_preview(
    dataframe: pd.DataFrame,
):
    """
    Build a frontend-friendly preview.
    """

    preview_dataframe = (
        dataframe
        .head(10)
        .copy()
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    preview_dataframe[
        "Training From Date"
    ] = preview_dataframe[
        "Training From Date"
    ].apply(
        lambda value: (
            parse_excel_date(
                value
            ).strftime(
                "%Y-%m-%d"
            )
            if parse_excel_date(
                value
            )
            else ""
        )
    )

    preview_dataframe[
        "Training To Date"
    ] = preview_dataframe[
        "Training To Date"
    ].apply(
        lambda value: (
            parse_excel_date(
                value
            ).strftime(
                "%Y-%m-%d"
            )
            if parse_excel_date(
                value
            )
            else ""
        )
    )

    # --------------------------------------------------------
    # Timing
    # --------------------------------------------------------

    preview_dataframe[
        "Timing"
    ] = preview_dataframe[
        "Timing"
    ].apply(
        lambda value: (
            parse_training_time(
                value
            ).strftime(
                "%H:%M"
            )
            if parse_training_time(
                value
            )
            else ""
        )
    )

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    preview_dataframe[
        "Duration of the Training Hours"
    ] = preview_dataframe[
        "Duration of the Training Hours"
    ].apply(
        lambda value: (
            parse_duration(
                value
            )
            if parse_duration(
                value
            ) is not None
            else ""
        )
    )

    # --------------------------------------------------------
    # Convert NaN
    # --------------------------------------------------------

    preview_dataframe = (
        preview_dataframe
        .fillna("")
    )

    return (
        preview_dataframe
        .to_dict(
            orient="records"
        )
    )


# ============================================================
# UPLOAD / VALIDATE / PREVIEW
# ============================================================

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
):
    """
    Validate and preview a training calendar.

    IMPORTANT:
        This endpoint does NOT write anything
        to PostgreSQL.
    """

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was selected.",
        )

    # --------------------------------------------------------
    # Extension
    # --------------------------------------------------------

    filename = (
        file.filename
        .lower()
    )

    if not filename.endswith(
        (
            ".xlsx",
            ".xls",
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files "
                "(.xlsx or .xls) are allowed."
            ),
        )

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    content = await file.read()

    if not content:

        raise HTTPException(
            status_code=400,
            detail="The Excel file is empty.",
        )

    # --------------------------------------------------------
    # Pandas
    # --------------------------------------------------------

    try:

        dataframe = pd.read_excel(
            BytesIO(content)
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to read the Excel file: "
                f"{str(error)}"
            ),
        )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validation = validate_dataframe(
        dataframe
    )

    # --------------------------------------------------------
    # Missing columns
    # --------------------------------------------------------

    if validation[
        "missing_columns"
    ]:

        return {
            "success": False,
            "message": (
                "Training calendar is missing "
                "required columns."
            ),
            "file_type": (
                "training_calendar"
            ),
            "filename": file.filename,
            "missing_columns": (
                validation[
                    "missing_columns"
                ]
            ),
            "extra_columns": (
                validation[
                    "extra_columns"
                ]
            ),
            "available_columns": (
                validation[
                    "available_columns"
                ]
            ),
            "errors": [],
        }

    # --------------------------------------------------------
    # Extra columns
    # --------------------------------------------------------

    if validation[
        "extra_columns"
    ]:

        return {
            "success": False,
            "message": (
                "The uploaded file contains "
                "columns that do not belong "
                "to the training calendar."
            ),
            "file_type": (
                "training_calendar"
            ),
            "filename": file.filename,
            "missing_columns": [],
            "extra_columns": (
                validation[
                    "extra_columns"
                ]
            ),
            "available_columns": (
                validation[
                    "available_columns"
                ]
            ),
            "errors": validation[
                "errors"
            ],
        }

    # --------------------------------------------------------
    # Row validation errors
    # --------------------------------------------------------

    if validation[
        "errors"
    ]:

        return {
            "success": False,
            "message": (
                "Training calendar contains "
                "validation errors."
            ),
            "file_type": (
                "training_calendar"
            ),
            "filename": file.filename,
            "total_rows": len(
                validation[
                    "dataframe"
                ]
            ),
            "missing_columns": [],
            "extra_columns": [],
            "errors": validation[
                "errors"
            ],
        }

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    dataframe = validation[
        "dataframe"
    ]

    preview = build_preview(
        dataframe
    )

    return {
        "success": True,
        "message": (
            "Training calendar validated "
            "successfully."
        ),
        "file_type": (
            "training_calendar"
        ),
        "filename": file.filename,
        "total_rows": len(
            dataframe
        ),
        "preview_rows": len(
            preview
        ),
        "columns": REQUIRED_COLUMNS,
        "preview": preview,
    }


# ============================================================
# IMPORT TRAINING CALENDAR
# ============================================================

@router.post("/import")
async def import_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    Import annual training calendar.

    HOD and Line Manager details are NOT read
    from this file.

    Those are maintained through Settings /
    Master Recipient Excel.
    """

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was selected.",
        )

    # --------------------------------------------------------
    # Extension
    # --------------------------------------------------------

    filename = (
        file.filename
        .lower()
    )

    if not filename.endswith(
        (
            ".xlsx",
            ".xls",
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files "
                "(.xlsx or .xls) are allowed."
            ),
        )

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    content = await file.read()

    if not content:

        raise HTTPException(
            status_code=400,
            detail="The Excel file is empty.",
        )

    try:

        dataframe = pd.read_excel(
            BytesIO(content)
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to read the Excel file: "
                f"{str(error)}"
            ),
        )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validation = validate_dataframe(
        dataframe
    )

    # --------------------------------------------------------
    # Missing columns
    # --------------------------------------------------------

    if validation[
        "missing_columns"
    ]:

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Training calendar is missing "
                    "required columns."
                ),
                "missing_columns": (
                    validation[
                        "missing_columns"
                    ]
                ),
                "extra_columns": (
                    validation[
                        "extra_columns"
                    ]
                ),
                "available_columns": (
                    validation[
                        "available_columns"
                    ]
                ),
                "errors": [],
            },
        )

    # --------------------------------------------------------
    # Extra columns
    # --------------------------------------------------------

    if validation[
        "extra_columns"
    ]:

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "The uploaded file contains "
                    "unsupported extra columns."
                ),
                "missing_columns": [],
                "extra_columns": (
                    validation[
                        "extra_columns"
                    ]
                ),
                "available_columns": (
                    validation[
                        "available_columns"
                    ]
                ),
                "errors": validation[
                    "errors"
                ],
            },
        )

    # --------------------------------------------------------
    # Validation errors
    # --------------------------------------------------------

    if validation[
        "errors"
    ]:

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Training calendar contains "
                    "validation errors."
                ),
                "errors": validation[
                    "errors"
                ],
            },
        )

    dataframe = validation[
        "dataframe"
    ]

    # ========================================================
    # IMPORT COUNTERS
    # ========================================================

    imported_rows = 0

    created_trainings = 0
    updated_trainings = 0

    training_ids = []

    audience_errors = []
    audience_cache = {}

    # ========================================================
    # PRE-CHECK ALL TARGET AUDIENCES
    # ========================================================
    #
    # Target Audience is the master relationship shared by:
    #
    #   Training.audience_id
    #   HOD.audience_id
    #   LineManager.audience_id
    #
    # HOD and Line Manager records are maintained through the
    # Settings / Master Recipient Excel. Therefore the calendar
    # import only resolves an existing Target Audience.
    # ========================================================

    for index, row in dataframe.iterrows():

        target_audience = str(
            clean_value(
                row["Target Audience"]
            )
        ).strip()

        cache_key = target_audience.lower()

        if cache_key in audience_cache:
            continue

        audience = await resolve_target_audience(
            db=db,
            target_audience=target_audience,
        )

        if audience is None:
            audience_errors.append(
                {
                    "row": index + 2,
                    "target_audience": target_audience,
                    "message": (
                        f"Target Audience '{target_audience}' "
                        "does not exist in the Target Audience "
                        "master table. Upload it through Settings "
                        "before importing the training calendar."
                    ),
                }
            )
        else:
            audience_cache[cache_key] = audience

    # --------------------------------------------------------
    # Stop before database modification
    # --------------------------------------------------------

    if audience_errors:

        return {
            "success": False,
            "message": (
                "Import cannot continue because one or more "
                "Target Audience values are not configured "
                "in Settings."
            ),
            "target_audience_errors": audience_errors,
            "hint": (
                "Add the Target Audience and its HOD / Line "
                "Manager recipients through the Settings "
                "Master Recipient Excel, then retry the import."
            ),
        }

    # ========================================================
    # DATABASE IMPORT
    # ========================================================

    try:

        for index, row in dataframe.iterrows():

            # ------------------------------------------------
            # Read Excel values
            # ------------------------------------------------

            serial_number = (
                parse_serial_number(
                    row["S.No"]
                )
            )

            training_name = str(
                clean_value(
                    row[
                        "Training Topic"
                    ]
                )
            ).strip()

            training_type = str(
                clean_value(
                    row[
                        "Training Type"
                    ]
                )
            ).strip()

            target_audience = str(
                clean_value(
                    row[
                        "Target Audience"
                    ]
                )
            ).strip()

            trainer_name = str(
                clean_value(
                    row[
                        "Trainer's Name"
                    ]
                )
            ).strip()

            scheduled_date = (
                parse_excel_date(
                    row[
                        "Training From Date"
                    ]
                )
            )

            scheduled_end_date = (
                parse_excel_date(
                    row[
                        "Training To Date"
                    ]
                )
            )

            scheduled_time = (
                parse_training_time(
                    row[
                        "Timing"
                    ]
                )
            )

            duration_hours = (
                parse_duration(
                    row[
                        "Duration of the Training Hours"
                    ]
                )
            )

            venue = str(
                clean_value(
                    row[
                        "Venue"
                    ]
                )
            ).strip()

            # ------------------------------------------------
            # Resolve Target Audience
            # ------------------------------------------------

            audience = audience_cache.get(
                target_audience.lower()
            )

            if audience is None:

                audience = await resolve_target_audience(
                    db=db,
                    target_audience=target_audience,
                )

                if audience is None:
                    raise ValueError(
                        f"Row {index + 2}: Target Audience "
                        f"'{target_audience}' does not exist "
                        "in the Target Audience master table."
                    )

                audience_cache[target_audience.lower()] = audience

            # =================================================
            # FIND EXISTING TRAINING
            # =================================================

            result = await db.execute(
                select(Training).where(
                    Training.training_name == training_name,
                    Training.audience_id == audience.id,
                    Training.scheduled_date == scheduled_date,
                )
            )

            training = result.scalar_one_or_none()

            # =================================================
            # CREATE TRAINING
            # =================================================

            if training is None:

                now = datetime.utcnow()

                training = Training(
                    training_name=training_name,
                    training_type=training_type,
                    department_id=None,
                    audience_id=audience.id,
                    scheduled_date=scheduled_date,
                    training_to_date=scheduled_end_date,
                    scheduled_time=scheduled_time,
                    duration_hours=duration_hours,
                    venue=venue,
                    status="SCHEDULED",
                    is_department_wise=False,
                    attendance_required=True,
                    ojt_required=False,
                    trainer_name=trainer_name,
                    created_at=now,
                    updated_at=now,
                )

                db.add(training)
                await db.flush()
                created_trainings += 1

            # =================================================
            # UPDATE EXISTING TRAINING
            # =================================================

            else:

                training.training_type = training_type
                training.audience_id = audience.id
                training.scheduled_date = scheduled_date
                training.training_to_date = scheduled_end_date
                training.scheduled_time = scheduled_time
                training.duration_hours = duration_hours
                training.venue = venue
                training.trainer_name = trainer_name
                training.updated_at = datetime.utcnow()

                updated_trainings += 1

            # ------------------------------------------------
            # Flush
            # ------------------------------------------------

            await db.flush()

            training_ids.append(
                training.id
            )

            imported_rows += 1

        # ====================================================
        # COMMIT
        # ====================================================

        await db.commit()

    except Exception as error:

        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Training calendar import failed: "
                f"{str(error)}"
            ),
        )

    # ========================================================
    # REMOVE DUPLICATE TRAINING IDS
    # ========================================================

    training_ids = list(
        dict.fromkeys(
            training_ids
        )
    )

    # ========================================================
    # GENERATE REMINDERS
    # ========================================================

    reminders_created = 0
    reminder_errors = []
    reminder_results = []

    for training_id in training_ids:

        result = (
            await generate_reminders_for_training(
                training_id
            )
        )

        reminder_results.append(
            result
        )

        reminders_created += int(
            result.get(
                "reminders_created",
                0,
            )
        )

        if not result.get(
            "success",
            False,
        ):

            reminder_errors.append(
                {
                    "training_id":
                        training_id,

                    "error":
                        result.get(
                            "error"
                        ),
                }
            )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "success": True,

        "message": (
            "Training calendar imported "
            "successfully."
        ),

        "filename": file.filename,

        "file_type":
            "training_calendar",

        "imported_rows":
            imported_rows,

        "created_trainings":
            created_trainings,

        "updated_trainings":
            updated_trainings,

        "reminders_created":
            reminders_created,

        "reminder_errors":
            reminder_errors,

        "reminder_results":
            reminder_results,
    }