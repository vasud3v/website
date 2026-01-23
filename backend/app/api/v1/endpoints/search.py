from fastapi import APIRouter, Query
from typing import List
from app.models.video import VideoListItem
from app.services.video_service import video_service

router = APIRouter()

@router.get("", response_model=List[VideoListItem])
async def search_videos(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Search videos by title or code"""
    return video_service.search_videos(q, limit)
