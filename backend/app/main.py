from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.routers import (
    auth,
    excel,
    training,
    post_training,
    reminder,
    reminder_engine,
)


app = FastAPI(
    title=settings.APP_NAME
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False,
)


app.include_router(auth.router)
app.include_router(excel.router)
app.include_router(training.router)
app.include_router(post_training.router)
app.include_router(reminder.router)
app.include_router(reminder_engine.router)


@app.get("/")
async def root():
    return {
        "message": settings.APP_NAME
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }