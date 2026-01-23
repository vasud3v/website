from fastapi import APIRouter
from app.api.v1.endpoints import videos, categories, studios, cast, search

api_router = APIRouter()

api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(studios.router, prefix="/studios", tags=["studios"])
api_router.include_router(cast.router, prefix="/cast", tags=["cast"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
