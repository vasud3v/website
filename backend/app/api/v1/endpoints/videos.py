from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.video import VideoDetail, PaginatedVideos, HomeFeed
from app.services.video_service import video_service

router = APIRouter()

@router.get("", response_model=PaginatedVideos)
async def get_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    studio: Optional[str] = None,
    actress: Optional[str] = None
):
    """Get paginated videos with optional filters"""
    return video_service.get_videos(
        page=page,
        limit=limit,
        search=search,
        category=category,
        studio=studio,
        actress=actress
    )

@router.get("/feed/home", response_model=HomeFeed)
async def get_home_feed(user_id: Optional[str] = None):
    """Get curated home feed"""
    return video_service.get_home_feed()

@router.get("/trending", response_model=PaginatedVideos)
async def get_trending_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get trending videos (sorted by views)"""
    return video_service.get_videos(
        page=page,
        limit=page_size,
        sort_by='views',
        sort_order='desc'
    )

@router.get("/popular", response_model=PaginatedVideos)
async def get_popular_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get popular videos (sorted by likes)"""
    return video_service.get_videos(
        page=page,
        limit=page_size,
        sort_by='likes',
        sort_order='desc'
    )

@router.get("/{code}", response_model=VideoDetail)
async def get_video(code: str):
    """Get single video by code"""
    video = video_service.get_video_by_code(code)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
