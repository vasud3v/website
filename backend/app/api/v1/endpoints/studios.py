from fastapi import APIRouter
from typing import List
from app.models.video import Studio
from app.services.video_service import video_service

router = APIRouter()

@router.get("", response_model=List[Studio])
async def get_studios():
    """Get all studios with video counts"""
    return video_service.get_studios()
