from datetime import datetime, timedelta



from sqlalchemy import create_engine, select, text

from sqlalchemy.orm import Session



from app.celery_app import celery_app

from app.core.config import settings



from app.models.hod import HOD

from app.models.line_manager import LineManager

from app.models.reminder import Reminder

from app.models.training_document import TrainingDocument

from app.models.whatsapp_template import WhatsAppTemplate



from app.services.email_service import send_email

from app.services.whatsapp_service import (

    send_whatsapp_message,

)





# ============================================================

# SYNC DATABASE

# ============================================================



celery_engine = create_engine(

    settings.SYNC_DATABASE_URL,

    echo=True,

    pool_pre_ping=True,

)





# ============================================================

# WHATSAPP TEMPLATE MAPPING

# ============================================================



TEMPLATE_TYPE_MAP = {

    # --------------------------------------------------------

    # PRE TRAINING

    # --------------------------------------------------------



    "MONTHLY":

        "TRAINING_REMINDER",



    "WEEKLY":

        "TRAINING_REMINDER",



    "BEFORE_TRAINING":

        "TRAINING_REMINDER",



    "BEFORE_TRAINING_7_DAYS":

        "TRAINING_REMINDER",



    "BEFORE_TRAINING_2_DAYS":

        "TRAINING_REMINDER",



    "BEFORE_TRAINING_1_DAY":

        "TRAINING_REMINDER",



    # --------------------------------------------------------

    # OLD TYPES

    # --------------------------------------------------------



    "DOCUMENT_SUBMISSION":

        "ATTENDANCE_REMINDER",



    "POST_TRAINING":

        "TRAINING_REPORT_REMINDER",



    # --------------------------------------------------------

    # OTHER EXISTING TYPES

    # --------------------------------------------------------



    "TRAINING_PERCENTAGE":

        "TRAINING_PERCENTAGE_REPORT",



    "OJT_REPORT":

        "OJT_REPORT_REMINDER",

}





# ============================================================

# GET WHATSAPP TEMPLATE TYPE

# ============================================================



def get_whatsapp_template_type(

    reminder_type: str,

):

    """

    Convert the reminder type into the

    WhatsApp template type.



    New post-training types are supported.

    """



    reminder_type = (

        reminder_type

        .strip()

        .upper()

    )



    # --------------------------------------------------------

    # New pre-training reminders

    # --------------------------------------------------------



    if reminder_type.startswith(

        "BEFORE_TRAINING_"

    ):

        return "TRAINING_REMINDER"



    # --------------------------------------------------------

    # New post-training reminders

    # --------------------------------------------------------



    if reminder_type.startswith(

        "POST_TRAINING_"

    ):



        if reminder_type.endswith(

            "_OJT_REPORT"

        ):

            return "OJT_REPORT_REMINDER"



        if reminder_type.endswith(

            "_ATTENDANCE"

        ):

            return "ATTENDANCE_REMINDER"



        if reminder_type.endswith(

            "_DOCUMENT"

        ):

            return "TRAINING_REPORT_REMINDER"



        return "TRAINING_REPORT_REMINDER"



    # --------------------------------------------------------

    # Existing mapping

    # --------------------------------------------------------



    template_type = (

        TEMPLATE_TYPE_MAP.get(

            reminder_type

        )

    )



    if not template_type:



        raise ValueError(

            "No WhatsApp template mapping "

            f"found for reminder type: "

            f"{reminder_type}"

        )



    return template_type





# ============================================================

# RESOLVE RECIPIENT

# ============================================================



def resolve_recipient(

    db: Session,

    recipient_type: str,

    recipient_id: int | None,

) -> dict:



    recipient_type = (

        recipient_type

        .strip()

        .upper()

    )



    if recipient_id is None:



        raise ValueError(

            f"recipient_id is required "

            f"for {recipient_type}"

        )



    # --------------------------------------------------------

    # HOD

    # --------------------------------------------------------



    if recipient_type == "HOD":



        recipient = db.execute(

            select(HOD).where(

                HOD.id == recipient_id

            )

        ).scalar_one_or_none()



    # --------------------------------------------------------

    # LINE MANAGER

    # --------------------------------------------------------



    elif recipient_type == "LINE_MANAGER":



        recipient = db.execute(

            select(LineManager).where(

                LineManager.id

                == recipient_id

            )

        ).scalar_one_or_none()



    else:



        raise ValueError(

            "Unsupported recipient type: "

            f"{recipient_type}"

        )



    if not recipient:



        raise ValueError(

            f"{recipient_type} with ID "

            f"{recipient_id} was not found"

        )



    if not recipient.email:



        raise ValueError(

            f"{recipient_type} with ID "

            f"{recipient_id} has no email address"

        )



    return {

        "id": recipient.id,

        "name": recipient.name,

        "email": recipient.email,

        "whatsapp_number": (

            recipient.whatsapp_number

        ),

        "department_id": (

            recipient.department_id

        ),

    }





# ============================================================

# GET DEFAULT WHATSAPP TEMPLATE

# ============================================================



def get_default_whatsapp_template(

    db: Session,

    reminder_type: str,

) -> WhatsAppTemplate:



    template_type = (

        get_whatsapp_template_type(

            reminder_type

        )

    )



    result = db.execute(

        select(WhatsAppTemplate)

        .where(

            WhatsAppTemplate.template_type

            == template_type,



            WhatsAppTemplate.is_default

            == True,



            WhatsAppTemplate.is_active

            == True,

        )

        .limit(1)

    )



    template = (

        result.scalar_one_or_none()

    )



    if not template:



        raise ValueError(

            "No active default WhatsApp "

            f"template found for "

            f"{template_type}"

        )



    return template





# ============================================================

# GET TRAINING DETAILS

# ============================================================



def get_training_details(

    db: Session,

    training_id: int,

) -> dict:



    result = db.execute(

        text(

            """

            SELECT

                t.id,

                t.training_name,

                t.scheduled_date,

                t.scheduled_time,

                t.trainer_name,

                t.department_id,

                t.audience_id,

                t.attendance_required,

                t.ojt_required,

                t.status,

                d.name AS department_name,

                ta.name AS audience_name



            FROM trainings t



            LEFT JOIN departments d

                ON d.id = t.department_id



            LEFT JOIN target_audiences ta

                ON ta.id = t.audience_id



            WHERE t.id = :training_id

            """

        ),

        {

            "training_id": training_id

        },

    )



    row = result.mappings().first()



    if not row:



        raise ValueError(

            f"Training with ID "

            f"{training_id} was not found"

        )



    return dict(row)





# ============================================================

# FORMAT DATE

# ============================================================



def format_date(value) -> str:



    if value is None:

        return ""



    if hasattr(

        value,

        "strftime",

    ):



        return value.strftime(

            "%d %B %Y"

        )



    return str(value)





# ============================================================

# FORMAT TIME

# ============================================================



def format_time(value) -> str:



    if value is None:

        return ""



    if hasattr(

        value,

        "strftime",

    ):



        return value.strftime(

            "%I:%M %p"

        )



    return str(value)





# ============================================================

# TRAINING STATISTICS

# ============================================================



def get_training_statistics(
    db: Session,
    department_id: int | None,
) -> dict:
    if department_id is None:
        return {
            "total_trainings": 0,
            "completed_trainings": 0,
            "pending_trainings": 0,
            "not_conducted": 0,
            "completion_percentage": 0,
            "pending_count": 0,
        }

    result = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_trainings,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) AS completed_trainings,
                COUNT(
                    CASE
                        WHEN status IN ('PENDING', 'SCHEDULED', 'RESCHEDULED')
                        THEN 1
                    END
                ) AS pending_trainings
            FROM trainings
            WHERE department_id = :department_id
            """
        ),
        {"department_id": department_id},
    )

    row = result.mappings().first()

    if not row:
        return {
            "total_trainings": 0,
            "completed_trainings": 0,
            "pending_trainings": 0,
            "not_conducted": 0,
            "completion_percentage": 0,
            "pending_count": 0,
        }

    total = int(row["total_trainings"] or 0)
    completed = int(row["completed_trainings"] or 0)
    pending = int(row["pending_trainings"] or 0)
    not_conducted = max(total - completed - pending, 0)
    percentage = round((completed / total) * 100, 2) if total > 0 else 0

    return {
        "total_trainings": total,
        "completed_trainings": completed,
        "pending_trainings": pending,
        "not_conducted": not_conducted,
        "completion_percentage": percentage,
        "pending_count": pending,
    }


def build_template_variables(
    db: Session,
    reminder: Reminder,
    recipient: dict,
    training: dict,
) -> dict:
    scheduled_date = training.get("scheduled_date")
    scheduled_time = training.get("scheduled_time")

    department_name = (
        training.get("department_name")
        or training.get("audience_name")
        or "Training Audience"
    )

    statistics = get_training_statistics(
        db,
        training.get("department_id"),
    )

    deadline = ""
    if scheduled_date:
        deadline = format_date(scheduled_date + timedelta(days=1))

    return {
        "name": recipient.get("name") or "",
        "training_name": training.get("training_name") or "",
        "date": format_date(scheduled_date),
        "time": format_time(scheduled_time),
        "trainer": training.get("trainer_name") or "",
        "department": department_name,
        "deadline": deadline,
        "total_trainings": str(statistics["total_trainings"]),
        "completed_trainings": str(statistics["completed_trainings"]),
        "pending_trainings": str(statistics["pending_trainings"]),
        "not_conducted": str(statistics["not_conducted"]),
        "completion_percentage": str(statistics["completion_percentage"]),
        "pending_count": str(statistics["pending_count"]),
    }


def render_template_message(

    message: str,

    variables: dict,

) -> str:



    rendered = message



    for key, value in (

        variables.items()

    ):



        rendered = rendered.replace(

            "{{" + key + "}}",

            str(value),

        )



    return rendered





# ============================================================

# GET TEMPLATE VARIABLES

# ============================================================



def get_template_variables(
    template_message: str,
    variables: dict,
) -> list[str]:
    # Meta positional mappings differ by template family.
    if "{{7}}" in template_message:
        positional_mapping = [
            "name",
            "department",
            "total_trainings",
            "completed_trainings",
            "pending_trainings",
            "not_conducted",
            "completion_percentage",
        ]
    elif (
        "{{6}}" in template_message
        and "{{4}}" in template_message
        and "{{5}}" in template_message
    ):
        positional_mapping = [
            "name",
            "training_name",
            "date",
            "time",
            "trainer",
            "department",
        ]
    else:
        positional_mapping = [
            "name",
            "training_name",
            "date",
        ]

    result = []
    for index, variable_name in enumerate(positional_mapping, start=1):
        placeholder = f"{{{{{index}}}}}"
        if placeholder in template_message:
            result.append(str(variables.get(variable_name, "")))

    # Backward compatibility for named placeholders.
    if not result:
        named_variables = [
            "name",
            "training_name",
            "date",
            "time",
            "trainer",
            "department",
            "deadline",
            "total_trainings",
            "completed_trainings",
            "pending_trainings",
            "not_conducted",
            "completion_percentage",
            "pending_count",
        ]
        for variable_name in named_variables:
            placeholder = f"{{{{{variable_name}}}}}"
            if placeholder in template_message:
                result.append(str(variables.get(variable_name, "")))

    return result


def build_email(

    reminder: Reminder,

    recipient: dict,

    training: dict | None = None,

):



    reminder_type = (

        reminder.reminder_type

        .replace(

            "_",

            " ",

        )

        .title()

    )



    subject = (

        "Training Reminder - "

        f"{reminder_type}"

    )



    body = f"""

Hello {recipient['name']},



This is an automated training reminder from the Training Reminder Automation System.



Reminder Type:

{reminder_type}

"""



    if training:



        body += f"""



Training:

{training.get('training_name') or ''}



Date:

{format_date(training.get('scheduled_date'))}



Time:

{format_time(training.get('scheduled_time'))}



Trainer:

{training.get('trainer_name') or ''}



Department:

{training.get('department_name') or ''}

"""



    # --------------------------------------------------------

    # Document-specific message

    # --------------------------------------------------------



    reminder_upper = (

        reminder.reminder_type

        .upper()

    )



    if (

        "ATTENDANCE"

        in reminder_upper

    ):



        body += """



Required Action:

Please submit the training attendance.

"""



    elif (

        "OJT_REPORT"

        in reminder_upper

    ):



        body += """



Required Action:

Please submit the OJT report.

"""



    else:



        body += """



Please review the scheduled training details and take the required action.

"""



    body += """



This is an automated message.



Regards,

HR

Training Reminder Automation System

"""



    return subject, body





# ============================================================

# POST-TRAINING DOCUMENT TYPE

# ============================================================



def get_post_training_document_type(

    reminder_type: str,

):



    reminder_type = (

        reminder_type

        .strip()

        .upper()

    )



    if reminder_type.endswith(

        "_ATTENDANCE"

    ):



        return "ATTENDANCE"



    if reminder_type.endswith(

        "_OJT_REPORT"

    ):



        return "OJT_REPORT"



    return None





# ============================================================

# POST-TRAINING CHECK

# ============================================================



def is_post_training_reminder(

    reminder_type: str,

):



    return (

        reminder_type

        .strip()

        .upper()

        .startswith(

            "POST_TRAINING_"

        )

    )





# ============================================================

# GET DOCUMENT STATUS

# ============================================================



def get_document_status_sync(

    db: Session,

    training_id: int,

    document_type: str,

):



    result = db.execute(

        select(

            TrainingDocument

        ).where(

            TrainingDocument.training_id

            == training_id,



            TrainingDocument.document_type

            == document_type,

        )

    )



    document = (

        result.scalar_one_or_none()

    )



    if document is None:

        return "PENDING"



    return (

        str(document.status)

        .strip()

        .upper()

    )





# ============================================================

# DOCUMENT COMPLETE

# ============================================================



def document_is_complete(

    status: str,

):



    return status in {

        "RECEIVED",

        "DONE",

    }





# ============================================================

# CHECK ALL REQUIRED DOCUMENTS

# ============================================================



def all_required_documents_complete(

    db: Session,

    training: dict,

):



    required = []



    if training.get(

        "attendance_required"

    ):



        required.append(

            "ATTENDANCE"

        )



    if training.get(

        "ojt_required"

    ):



        required.append(

            "OJT_REPORT"

        )



    if not required:

        return True



    for document_type in required:



        status = (

            get_document_status_sync(

                db,

                training["id"],

                document_type,

            )

        )



        if not document_is_complete(

            status

        ):



            return False



    return True





# ============================================================

# CREATE NEXT WEEKLY REMINDER

# ============================================================



def create_next_weekly_reminder(

    db: Session,

    reminder: Reminder,

):



    document_type = (

        get_post_training_document_type(

            reminder.reminder_type

        )

    )



    if not document_type:

        return None



    # --------------------------------------------------------

    # Check current document

    # --------------------------------------------------------



    document_status = (

        get_document_status_sync(

            db,

            reminder.training_id,

            document_type,

        )

    )



    if document_is_complete(

        document_status

    ):



        print(

            "[WEEKLY REMINDER NOT CREATED] "

            f"training={reminder.training_id} "

            f"document={document_type} "

            f"status={document_status}"

        )



        return None



    # --------------------------------------------------------

    # Next weekly date

    # --------------------------------------------------------



    next_scheduled_at = (

        reminder.scheduled_at

        + timedelta(days=7)

    )



    next_reminder_type = (

        "POST_TRAINING_WEEKLY_"

        f"{document_type}"

    )



    # --------------------------------------------------------

    # Duplicate check

    # --------------------------------------------------------



    existing = db.execute(

        select(Reminder).where(

            Reminder.training_id

            == reminder.training_id,



            Reminder.reminder_type

            == next_reminder_type,



            Reminder.recipient_type

            == reminder.recipient_type,



            Reminder.recipient_id

            == reminder.recipient_id,



            Reminder.channel

            == reminder.channel,



            Reminder.scheduled_at

            == next_scheduled_at,

        )

    ).scalar_one_or_none()



    if existing:



        return existing



    # --------------------------------------------------------

    # Create next reminder

    # --------------------------------------------------------



    next_reminder = Reminder(

        training_id=(

            reminder.training_id

        ),



        reminder_type=(

            next_reminder_type

        ),



        recipient_type=(

            reminder.recipient_type

        ),



        recipient_id=(

            reminder.recipient_id

        ),



        channel=(

            reminder.channel

        ),



        scheduled_at=(

            next_scheduled_at

        ),



        status="PENDING",

    )



    db.add(

        next_reminder

    )



    print(

        "[WEEKLY REMINDER CREATED] "

        f"training={reminder.training_id} "

        f"document={document_type} "

        f"recipient="

        f"{reminder.recipient_type}:"

        f"{reminder.recipient_id} "

        f"channel={reminder.channel} "

        f"scheduled="

        f"{next_scheduled_at}"

    )



    return next_reminder





# ============================================================

# CANCEL FUTURE REMINDERS FOR DOCUMENT

# ============================================================



def cancel_pending_document_reminders(

    db: Session,

    training_id: int,

    document_type: str,

):



    result = db.execute(

        select(Reminder).where(

            Reminder.training_id

            == training_id,



            Reminder.status

            == "PENDING",

        )

    )



    reminders = (

        result.scalars().all()

    )



    cancelled = 0



    for reminder in reminders:



        if not is_post_training_reminder(

            reminder.reminder_type

        ):

            continue



        reminder_document_type = (

            get_post_training_document_type(

                reminder.reminder_type

            )

        )



        if (

            reminder_document_type

            != document_type

        ):

            continue



        reminder.status = (

            "CANCELLED"

        )



        reminder.failure_reason = (

            f"{document_type} submitted. "

            "Future reminder cancelled."

        )



        cancelled += 1



        print(

            "[REMINDER CANCELLED] "

            f"id={reminder.id} "

            f"training={training_id} "

            f"document={document_type}"

        )



    return cancelled





# ============================================================

# CELERY TASK

# ============================================================



@celery_app.task(

    name=(

        "app.tasks.reminder_tasks."

        "process_due_reminders"

    )

)

def process_due_reminders():



    now = datetime.now()



    with Session(

        celery_engine

    ) as db:



        result = db.execute(

            select(Reminder)

            .where(

                Reminder.status

                == "PENDING",



                Reminder.scheduled_at

                <= now,

            )

            .order_by(

                Reminder.scheduled_at

            )

        )



        reminders = (

            result.scalars().all()

        )



        processed = 0



        for reminder in reminders:



            try:



                # =================================================

                # GET TRAINING FIRST

                # =================================================



                training = (

                    get_training_details(

                        db,

                        reminder.training_id,

                    )

                )



                # =================================================

                # STOP POST-TRAINING REMINDER

                # IF DOCUMENT ALREADY SUBMITTED

                # =================================================



                if is_post_training_reminder(

                    reminder.reminder_type

                ):



                    document_type = (

                        get_post_training_document_type(

                            reminder.reminder_type

                        )

                    )



                    if document_type:



                        document_status = (

                            get_document_status_sync(

                                db,

                                reminder.training_id,

                                document_type,

                            )

                        )



                        print(

                            "[DOCUMENT CHECK] "

                            f"training="

                            f"{reminder.training_id} "

                            f"document="

                            f"{document_type} "

                            f"status="

                            f"{document_status}"

                        )



                        if document_is_complete(

                            document_status

                        ):



                            reminder.status = (

                                "CANCELLED"

                            )



                            reminder.failure_reason = (

                                f"{document_type} "

                                "already submitted. "

                                "Reminder cancelled."

                            )



                            print(

                                "[REMINDER CANCELLED] "

                                f"id={reminder.id}"

                            )



                            continue



                # =================================================

                # CHECK ALL REQUIRED DOCUMENTS

                # =================================================



                if (

                    is_post_training_reminder(

                        reminder.reminder_type

                    )

                    and all_required_documents_complete(

                        db,

                        training,

                    )

                ):



                    reminder.status = (

                        "CANCELLED"

                    )



                    reminder.failure_reason = (

                        "All required "

                        "post-training documents "

                        "submitted."

                    )



                    print(

                        "[ALL DOCUMENTS COMPLETE] "

                        f"training="

                        f"{reminder.training_id}"

                    )



                    continue



                # =================================================

                # LOG

                # =================================================



                print(

                    "[REMINDER DUE] "

                    f"id={reminder.id} "

                    f"type={reminder.reminder_type} "

                    f"channel={reminder.channel} "

                    f"recipient="

                    f"{reminder.recipient_type}:"

                    f"{reminder.recipient_id}"

                )



                # =================================================

                # RESOLVE RECIPIENT

                # =================================================



                recipient = (

                    resolve_recipient(

                        db,

                        reminder.recipient_type,

                        reminder.recipient_id,

                    )

                )



                print(

                    "[RECIPIENT RESOLVED] "

                    f"{recipient['name']} | "

                    f"email="

                    f"{recipient['email']} | "

                    f"whatsapp="

                    f"{recipient['whatsapp_number']}"

                )



                # =================================================

                # MARK PROCESSING

                # =================================================



                reminder.status = (

                    "PROCESSING"

                )



                db.flush()



                channel = (

                    reminder.channel

                    .strip()

                    .upper()

                )



                # =================================================

                # EMAIL

                # =================================================



                if channel == "EMAIL":



                    subject, body = (

                        build_email(

                            reminder,

                            recipient,

                            training,

                        )

                    )



                    send_email(

                        to_email=(

                            recipient[

                                "email"

                            ]

                        ),



                        subject=subject,



                        body=body,

                    )



                    reminder.status = (

                        "SENT"

                    )



                    reminder.sent_at = (

                        datetime.now()

                    )



                    reminder.failure_reason = (

                        None

                    )



                    print(

                        "[EMAIL SENT] "

                        f"reminder_id="

                        f"{reminder.id} "

                        f"to="

                        f"{recipient['email']}"

                    )



                # =================================================

                # WHATSAPP

                # =================================================



                elif channel == "WHATSAPP":



                    whatsapp_number = (

                        recipient[

                            "whatsapp_number"

                        ]

                    )



                    if not whatsapp_number:



                        raise ValueError(

                            f"{reminder.recipient_type} "

                            f"with ID "

                            f"{reminder.recipient_id} "

                            "has no WhatsApp number"

                        )



                    # -------------------------------------------------

                    # TEMPLATE

                    # -------------------------------------------------



                    template = (

                        get_default_whatsapp_template(

                            db,

                            reminder.reminder_type,

                        )

                    )



                    print(

                        "[WHATSAPP TEMPLATE] "

                        f"id={template.id} "

                        f"type="

                        f"{template.template_type} "

                        f"name="

                        f"{template.name} "

                        f"meta_name="

                        f"{template.meta_template_name}"

                    )



                    # -------------------------------------------------

                    # VARIABLES

                    # -------------------------------------------------



                    variables = (

                        build_template_variables(

                            db,

                            reminder,

                            recipient,

                            training,

                        )

                    )



                    rendered_message = (

                        render_template_message(

                            template.message,

                            variables,

                        )

                    )



                    print(

                        "[WHATSAPP RENDERED MESSAGE] "

                        f"{rendered_message}"

                    )



                    template_variables = (

                        get_template_variables(

                            template.message,

                            variables,

                        )

                    )



                    print(

                        "[WHATSAPP VARIABLES] "

                        f"{template_variables}"

                    )



                    # -------------------------------------------------

                    # META TEMPLATE PARAMETERS

                    # -------------------------------------------------



                    if (

                        template.meta_template_name

                        == "hello_world"

                    ):



                        meta_variables = None



                    else:



                        meta_variables = (

                            template_variables

                        )



                    # -------------------------------------------------

                    # SEND WHATSAPP

                    # -------------------------------------------------



                    response = (

                        send_whatsapp_message(

                            to_phone=(

                                whatsapp_number

                            ),



                            message_text=(

                                rendered_message

                            ),



                            template_name=(

                                template.meta_template_name

                            ),



                            language_code=(

                                template.language_code

                            ),



                            variables=(

                                meta_variables

                            ),

                        )

                    )



                    # -------------------------------------------------

                    # STORE MESSAGE ID

                    # -------------------------------------------------



                    messages = response.get(

                        "messages",

                        [],

                    )



                    if messages:



                        reminder.whatsapp_message_id = (

                            messages[0].get(

                                "id"

                            )

                        )



                        print(

                            "[WHATSAPP MESSAGE ID] "

                            f"reminder_id="

                            f"{reminder.id} "

                            f"message_id="

                            f"{reminder.whatsapp_message_id}"

                        )



                    # -------------------------------------------------

                    # SENT

                    # -------------------------------------------------



                    reminder.status = (

                        "SENT"

                    )



                    reminder.sent_at = (

                        datetime.now()

                    )



                    reminder.failure_reason = (

                        None

                    )



                    print(

                        "[WHATSAPP SENT] "

                        f"reminder_id="

                        f"{reminder.id} "

                        f"to="

                        f"{whatsapp_number}"

                    )



                    print(

                        "[WHATSAPP RESPONSE] "

                        f"{response}"

                    )



                # =================================================

                # INVALID CHANNEL

                # =================================================



                else:



                    raise ValueError(

                        "Unsupported channel: "

                        f"{reminder.channel}"

                    )



                # =================================================

                # CREATE NEXT WEEKLY REMINDER

                # =================================================



                if (

                    reminder.status

                    == "SENT"

                    and is_post_training_reminder(

                        reminder.reminder_type

                    )

                    and (

                        reminder.reminder_type.endswith(

                            "_7_DAYS_ATTENDANCE"

                        )

                        or

                        reminder.reminder_type.endswith(

                            "_7_DAYS_OJT_REPORT"

                        )

                        or

                        reminder.reminder_type.endswith(

                            "_WEEKLY_ATTENDANCE"

                        )

                        or

                        reminder.reminder_type.endswith(

                            "_WEEKLY_OJT_REPORT"

                        )

                    )

                ):



                    create_next_weekly_reminder(

                        db,

                        reminder,

                    )



                processed += 1



            except Exception as exc:



                reminder.status = (

                    "FAILED"

                )



                reminder.failure_reason = (

                    str(exc)

                )



                print(

                    "[REMINDER FAILED] "

                    f"id={reminder.id} "

                    f"reason={exc}"

                )



        # =========================================================

        # COMMIT

        # =========================================================



        db.commit()



        print(

            "[REMINDER ENGINE] "

            f"Processed {processed} "

            "reminder(s)."

        )



        return {

            "processed":

                processed

        }