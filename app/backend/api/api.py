from fastapi import APIRouter

from app.backend.api.endpoints import resources, server


api_router = APIRouter()

api_router.include_router(resources.router, prefix="/resources", tags=["Resources"])
api_router.include_router(server.router, prefix="/server", tags=["Server"])
