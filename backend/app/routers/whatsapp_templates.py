from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.whatsapp_template import WhatsAppTemplate


router = APIRouter(
    prefix="/api/whatsapp-templates",
    tags=["WhatsApp Templates"],
)


# =========================================================
# Supported template types
# =========================================================

TEMPLATE_TYPES = {
    "TRAINING_REMINDER",
    "ATTENDANCE_REMINDER",
    "OJT_REPORT_REMINDER",
    "TRAINING_REPORT_REMINDER",
    "TRAINING_PERCENTAGE_REPORT",
}


# =========================================================
# Request Models
# =========================================================

class WhatsAppTemplateCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    template_type: str = Field(
        min_length=1,
        max_length=50,
    )

    meta_template_name: str = Field(
        min_length=1,
        max_length=100,
    )

    language_code: str = "en_US"

    message: str = Field(
        min_length=1,
    )

    is_default: bool = False


class WhatsAppTemplateUpdate(BaseModel):

    name: str | None = None

    template_type: str | None = None

    meta_template_name: str | None = None

    language_code: str | None = None

    message: str | None = None

    is_default: bool | None = None

    is_active: bool | None = None


# =========================================================
# Validation
# =========================================================

def validate_template_type(
    template_type: str,
):

    template_type = template_type.strip().upper()

    if template_type not in TEMPLATE_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid template_type: {template_type}. "
                f"Supported types: "
                f"{', '.join(sorted(TEMPLATE_TYPES))}"
            ),
        )

    return template_type


# =========================================================
# GET ALL TEMPLATES
# =========================================================

@router.get("")
async def get_templates(
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(WhatsAppTemplate)
        .order_by(
            WhatsAppTemplate.template_type,
            WhatsAppTemplate.is_default.desc(),
            WhatsAppTemplate.created_at.desc(),
        )
    )

    templates = result.scalars().all()

    return {
        "value": [
            {
                "id": template.id,
                "name": template.name,
                "template_type": template.template_type,
                "meta_template_name": template.meta_template_name,
                "language_code": template.language_code,
                "message": template.message,
                "is_default": template.is_default,
                "is_active": template.is_active,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
            }
            for template in templates
        ],
        "Count": len(templates),
    }


# =========================================================
# GET DEFAULT TEMPLATE
# =========================================================

@router.get("/default/{template_type}")
async def get_default_template(
    template_type: str,
    db: AsyncSession = Depends(get_db),
):

    template_type = validate_template_type(
        template_type
    )

    result = await db.execute(
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

    template = result.scalar_one_or_none()

    if not template:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No default WhatsApp template "
                f"found for {template_type}"
            ),
        )

    return {
        "id": template.id,
        "name": template.name,
        "template_type": template.template_type,
        "meta_template_name": template.meta_template_name,
        "language_code": template.language_code,
        "message": template.message,
        "is_default": template.is_default,
        "is_active": template.is_active,
    }


# =========================================================
# CREATE TEMPLATE
# =========================================================

@router.post("")
async def create_template(
    data: WhatsAppTemplateCreate,
    db: AsyncSession = Depends(get_db),
):

    template_type = validate_template_type(
        data.template_type
    )

    # -----------------------------------------------------
    # If this template becomes default,
    # remove default from other templates of SAME TYPE.
    # -----------------------------------------------------

    if data.is_default:

        result = await db.execute(
            select(WhatsAppTemplate)
            .where(
                WhatsAppTemplate.template_type
                == template_type,

                WhatsAppTemplate.is_default
                == True,
            )
        )

        existing_defaults = result.scalars().all()

        for existing in existing_defaults:
            existing.is_default = False

    template = WhatsAppTemplate(
        name=data.name,
        template_type=template_type,
        meta_template_name=data.meta_template_name,
        language_code=data.language_code,
        message=data.message,
        is_default=data.is_default,
        is_active=True,
    )

    db.add(template)

    await db.commit()

    await db.refresh(template)

    return {
        "success": True,
        "message": "WhatsApp template created successfully",
        "template": {
            "id": template.id,
            "name": template.name,
            "template_type": template.template_type,
            "meta_template_name": template.meta_template_name,
            "language_code": template.language_code,
            "message": template.message,
            "is_default": template.is_default,
            "is_active": template.is_active,
        },
    }


# =========================================================
# UPDATE TEMPLATE
# =========================================================

@router.put("/{template_id}")
async def update_template(
    template_id: int,
    data: WhatsAppTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(WhatsAppTemplate)
        .where(
            WhatsAppTemplate.id == template_id
        )
    )

    template = result.scalar_one_or_none()

    if not template:

        raise HTTPException(
            status_code=404,
            detail="WhatsApp template not found",
        )

    # -----------------------------------------------------
    # Determine template type
    # -----------------------------------------------------

    new_template_type = template.template_type

    if data.template_type is not None:

        new_template_type = validate_template_type(
            data.template_type
        )

    # -----------------------------------------------------
    # If becoming default, remove default from
    # other templates of SAME TYPE.
    # -----------------------------------------------------

    if data.is_default is True:

        result = await db.execute(
            select(WhatsAppTemplate)
            .where(
                WhatsAppTemplate.id != template_id,

                WhatsAppTemplate.template_type
                == new_template_type,

                WhatsAppTemplate.is_default
                == True,
            )
        )

        existing_defaults = result.scalars().all()

        for existing in existing_defaults:
            existing.is_default = False

    # -----------------------------------------------------
    # Update fields
    # -----------------------------------------------------

    if data.name is not None:
        template.name = data.name

    if data.template_type is not None:
        template.template_type = new_template_type

    if data.meta_template_name is not None:
        template.meta_template_name = (
            data.meta_template_name
        )

    if data.language_code is not None:
        template.language_code = (
            data.language_code
        )

    if data.message is not None:
        template.message = data.message

    if data.is_default is not None:
        template.is_default = data.is_default

    if data.is_active is not None:
        template.is_active = data.is_active

    await db.commit()

    await db.refresh(template)

    return {
        "success": True,
        "message": "WhatsApp template updated successfully",
        "template": {
            "id": template.id,
            "name": template.name,
            "template_type": template.template_type,
            "meta_template_name": template.meta_template_name,
            "language_code": template.language_code,
            "message": template.message,
            "is_default": template.is_default,
            "is_active": template.is_active,
        },
    }