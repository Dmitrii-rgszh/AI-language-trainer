from fastapi import APIRouter

from app.api.routes.adaptive import router as adaptive_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.diagnostic import router as diagnostic_router
from app.api.routes.grammar import router as grammar_router
from app.api.routes.health import router as health_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.listening import router as listening_router
from app.api.routes.mistakes import router as mistakes_router
from app.api.routes.profile import router as profile_router
from app.api.routes.profession import router as profession_router
from app.api.routes.progress import router as progress_router
from app.api.routes.pronunciation import router as pronunciation_router
from app.api.routes.providers import router as providers_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.speaking import router as speaking_router
from app.api.routes.voice import router as voice_router
from app.api.routes.writing import router as writing_router
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(health_router)
api_router.include_router(profile_router)
api_router.include_router(adaptive_router)
api_router.include_router(diagnostic_router)
api_router.include_router(dashboard_router)
api_router.include_router(lessons_router)
api_router.include_router(listening_router)
api_router.include_router(grammar_router)
api_router.include_router(speaking_router)
api_router.include_router(pronunciation_router)
api_router.include_router(voice_router)
api_router.include_router(writing_router)
api_router.include_router(profession_router)
api_router.include_router(progress_router)
api_router.include_router(mistakes_router)
api_router.include_router(recommendations_router)
api_router.include_router(providers_router)
