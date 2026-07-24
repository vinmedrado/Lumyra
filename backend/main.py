from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.middleware.request_context import RequestContextMiddleware
from backend.realtime.websocket_router import router as websocket_router
from services.logging_service import configure_logging
from core.settings import get_settings
from db.session import create_all
from repositories.database import init_db
from backend.routers import analytics, auth, events, guests, forms, messages, financial, insights, documents, health, automation, notifications, playlists, music_suggestions, public_portal

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    # Transitional portfolio mode: legacy repositories and SQLAlchemy share
    # the same SQLite file. PostgreSQL becomes supported only after the raw
    # sqlite3 repository has been fully migrated.
    if settings.is_sqlite:
        create_all()
    yield


app = FastAPI(title=f'{settings.APP_NAME} API', version=settings.APP_VERSION, lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(guests.router)
app.include_router(forms.router)
app.include_router(messages.router)
app.include_router(financial.router)
app.include_router(insights.router)
app.include_router(analytics.router)
app.include_router(documents.router)
app.include_router(health.router)
app.include_router(automation.router)
app.include_router(playlists.router)
app.include_router(music_suggestions.router)
app.include_router(public_portal.router)

app.include_router(notifications.router)
app.include_router(websocket_router)
