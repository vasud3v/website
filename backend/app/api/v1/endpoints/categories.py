from fastapi import APIRouter
from typing import List
from app.models.video import Category
from app.services.video_service import video_service

router = APIRouter()

@router.get("", response_model=List[Category])
async def get_categories():
    """Get all categories with video counts"""
    return video_service.get_categories()
