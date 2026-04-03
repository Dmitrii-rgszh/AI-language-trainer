import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.dependencies import live_avatar_service, welcome_tutor_service
from app.core.errors import AppError

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.on_event("startup")
async def prewarm_welcome_tutor() -> None:
    welcome_tutor_service.schedule_default_prewarm()
    asyncio.create_task(live_avatar_service.warmup())


@app.on_event("shutdown")
async def shutdown_live_avatar() -> None:
    await live_avatar_service.shutdown()


app.include_router(api_router)
