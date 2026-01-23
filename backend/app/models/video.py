from typing import List, Optional, Dict
from pydantic import BaseModel

class VideoListItem(BaseModel):
    """Video list item model"""
    code: str
    title: str
    thumbnail_url: str
    duration: str
    release_date: str
    studio: str = ""
    views: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    like_count: int = 0
    
    class Config:
        # Allow extra fields from database
        extra = "ignore"

class VideoDetail(VideoListItem):
    """Detailed video model"""
    content_id: Optional[str] = None
    cover_url: Optional[str] = None
    series: Optional[str] = None
    description: Optional[str] = None
    embed_urls: List[str] = []
    gallery_images: List[str] = []
    categories: List[str] = []
    cast: List[str] = []
    cast_images: Dict[str, str] = {}
    scraped_at: Optional[str] = None

class Video(VideoDetail):
    """Complete video model with all fields"""
    pass

class Category(BaseModel):
    """Category model"""
    name: str
    video_count: int
    thumbnail_url: Optional[str] = None

class Studio(BaseModel):
    """Studio model"""
    name: str
    video_count: int

class Cast(BaseModel):
    """Cast member model"""
    name: str
    video_count: int
    image_url: Optional[str] = None

class HomeFeed(BaseModel):
    """Home feed model"""
    featured: List[VideoListItem]
    trending: List[VideoListItem]
    popular: List[VideoListItem]
    top_rated: List[VideoListItem]
    new_releases: List[VideoListItem]
    classics: List[VideoListItem]

class PaginatedVideos(BaseModel):
    """Paginated videos response"""
    videos: List[VideoListItem]
    total: int
    page: int
    limit: int
    pages: int
