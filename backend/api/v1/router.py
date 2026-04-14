"""V1 aggregate router — includes all sub-routers under /api/v1."""

from fastapi import APIRouter

from api.v1.auth import router as auth_router
from api.v1.health import router as health_router
from api.v1.oauth import router as oauth_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(oauth_router)
