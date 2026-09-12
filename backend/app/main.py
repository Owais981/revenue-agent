import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine
from app.api import auth, leads, accounts, settings as settings_api, audit_logs, dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("revenue_agent")

# import models so they register on Base before create_all
from app import models  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, description="Revenue Agent - lead scoring, account research, next-best action")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    # Vite auto-increments the port when the default is taken, so any localhost port
    # is allowed in addition to the configured FRONTEND_URL rather than hardcoding one.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(accounts.router)
app.include_router(settings_api.router)
app.include_router(audit_logs.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"app": settings.app_name, "status": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
