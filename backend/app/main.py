from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings

from app.routers import (
    auth,
    excel,
    training,
    post_training,
    reminder,
    reminder_engine,
    recipients,
    reports,
    whatsapp_templates,
    departments,
)


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ==================================================
# CORS CONFIGURATION
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# SESSION MIDDLEWARE
# ==================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False,
)


# ==================================================
# ROUTERS
# ==================================================

app.include_router(auth.router)

app.include_router(excel.router)

app.include_router(training.router)

app.include_router(post_training.router)

app.include_router(reminder.router)

app.include_router(reminder_engine.router)

app.include_router(recipients.router)

app.include_router(reports.router)

app.include_router(whatsapp_templates.router)

# Departments
app.include_router(departments.router)


# ==================================================
# ROOT
# ==================================================

@app.get("/")
async def root():
    return {
        "message": settings.APP_NAME
    }


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }