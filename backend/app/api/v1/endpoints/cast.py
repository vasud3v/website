from fastapi import APIRouter
from typing import List
from app.models.video import Cast
from app.services.video_service import video_service

router = APIRouter()

@router.get("", response_model=List[Cast])
async def get_cast():
    """Get all cast members with video counts and images"""
    return video_service.get_cast()
