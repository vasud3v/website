from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from app.core.config import settings
from app.models.video import (
    Video, VideoListItem, VideoDetail, 
    Category, Studio, Cast, HomeFeed, PaginatedVideos
)

class VideoService:
    """Service for video operations"""
    
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        self._cache: Optional[List[Dict[str, Any]]] = None
    
    def _parse_number(self, value: Any) -> int:
        """Parse number from string or int"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            # Remove spaces and convert to int
            return int(value.replace(' ', '').replace(',', ''))
        return 0
    
    def _normalize_video(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize video data from database format"""
        normalized = video.copy()
        
        # Parse views and likes
        normalized['views'] = self._parse_number(video.get('views', 0))
        normalized['like_count'] = self._parse_number(video.get('likes', 0))
        
        # Set default studio if missing
        if 'studio' not in normalized or not normalized['studio']:
            normalized['studio'] = "Unknown"
        
        # Use models as cast if cast is missing
        if 'cast' not in normalized:
            normalized['cast'] = video.get('models', [])
        
        # Set default ratings
        if 'rating_avg' not in normalized or normalized['rating_avg'] is None:
            normalized['rating_avg'] = 0.0
        if 'rating_count' not in normalized or normalized['rating_count'] is None:
            normalized['rating_count'] = 0
        
        # Ensure required fields exist
        if 'thumbnail_url' not in normalized or not normalized['thumbnail_url']:
            # Try multiple fallback fields
            normalized['thumbnail_url'] = (
                video.get('thumbnail_original') or 
                video.get('cover_url') or 
                video.get('thumbnail') or 
                '/placeholder.jpg'
            )
        
        if 'duration' not in normalized or not normalized['duration']:
            normalized['duration'] = "0:00"
        
        if 'release_date' not in normalized or not normalized['release_date']:
            normalized['release_date'] = "Unknown"
        
        # Include preview_video_url if available
        if 'preview_video_url' in video and video['preview_video_url']:
            normalized['preview_video_url'] = video['preview_video_url']
        
        return normalized
    
    def _load_videos(self) -> List[Dict[str, Any]]:
        """Load videos from database with caching"""
        if self._cache is not None:
            return self._cache
        
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                    return self._cache
            return []
        except Exception as e:
            print(f"Error loading videos: {e}")
            return []
    
    def reload_cache(self):
        """Reload video cache"""
        self._cache = None
        return self._load_videos()
    
    def get_videos(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        studio: Optional[str] = None,
        actress: Optional[str] = None,
        sort_by: str = 'release_date',
        sort_order: str = 'desc'
    ) -> PaginatedVideos:
        """Get paginated videos with filters"""
        videos = self._load_videos()
        
        # Apply filters
        if search:
            search_lower = search.lower()
            videos = [v for v in videos if 
                      search_lower in v.get('title', '').lower() or 
                      search_lower in v.get('code', '').lower()]
        
        if category:
            videos = [v for v in videos if category in v.get('categories', [])]
        
        if studio:
            videos = [v for v in videos if v.get('studio', '').lower() == studio.lower()]
        
        if actress:
            cast = v.get('cast', v.get('models', []))
            videos = [v for v in videos if actress in cast]
        
        # Normalize videos first (for proper sorting)
        normalized = [self._normalize_video(v) for v in videos]
        
        # Sort videos
        reverse = sort_order == 'desc'
        if sort_by == 'views':
            normalized.sort(key=lambda x: x.get('views', 0), reverse=reverse)
        elif sort_by == 'likes':
            normalized.sort(key=lambda x: x.get('like_count', 0), reverse=reverse)
        elif sort_by == 'release_date':
            normalized.sort(key=lambda x: x.get('release_date', ''), reverse=reverse)
        elif sort_by == 'title':
            normalized.sort(key=lambda x: x.get('title', ''), reverse=reverse)
        
        # Pagination
        total = len(normalized)
        start = (page - 1) * limit
        end = start + limit
        paginated = normalized[start:end]
        
        return PaginatedVideos(
            videos=[VideoListItem(**v) for v in paginated],
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
    
    def get_video_by_code(self, code: str) -> Optional[VideoDetail]:
        """Get single video by code"""
        videos = self._load_videos()
        video = next((v for v in videos if v.get('code') == code), None)
        
        if video:
            normalized = self._normalize_video(video)
            return VideoDetail(**normalized)
        return None
    
    def get_home_feed(self) -> HomeFeed:
        """Get curated home feed"""
        videos = self._load_videos()
        
        if not videos:
            return HomeFeed(
                featured=[],
                trending=[],
                popular=[],
                top_rated=[],
                new_releases=[],
                classics=[]
            )
        
        # Normalize all videos first
        normalized_videos = [self._normalize_video(v) for v in videos]
        
        # Sort videos by different criteria (handle None values)
        featured = sorted(normalized_videos, key=lambda x: x.get('rating_avg', 0) * x.get('views', 0), reverse=True)[:10]
        trending = sorted(normalized_videos, key=lambda x: x.get('views', 0), reverse=True)[:10]
        popular = sorted(normalized_videos, key=lambda x: x.get('like_count', 0), reverse=True)[:10]
        top_rated = sorted(normalized_videos, key=lambda x: x.get('rating_avg', 0), reverse=True)[:10]
        new_releases = sorted(normalized_videos, key=lambda x: x.get('release_date') or '', reverse=True)[:10]
        classics = sorted(normalized_videos, key=lambda x: x.get('release_date') or 'ZZZZ')[:10]
        
        return HomeFeed(
            featured=[VideoListItem(**v) for v in featured],
            trending=[VideoListItem(**v) for v in trending],
            popular=[VideoListItem(**v) for v in popular],
            top_rated=[VideoListItem(**v) for v in top_rated],
            new_releases=[VideoListItem(**v) for v in new_releases],
            classics=[VideoListItem(**v) for v in classics]
        )
    
    def get_categories(self) -> List[Category]:
        """Get all categories with counts and static images from Jable"""
        videos = self._load_videos()
        
        # Map English category names to Jable image paths
        category_image_map = {
            "Roleplay": "/categories/角色劇情.jpg",
            "Chinese Subtitle": "/categories/中文字幕.jpg",
            "Uniform": "/categories/制服誘惑.jpg",
            "Pantyhose": "/categories/絲襪美腿.jpg",
            "Sex Only": "/categories/直接開啪.jpg",
            "Group Sex": "/categories/多p群交.jpg",
            "BDSM": "/categories/主奴調教.jpg",
            "POV": "/categories/男友視角.jpg",
            "Insult": "/categories/凌辱快感.jpg",
            "Private Cam": "/categories/盜攝偷拍.jpg",
        }
        
        # Standard Jable categories with their order
        standard_categories = [
            "Roleplay", "Chinese Subtitle", "Uniform", "Pantyhose",
            "Sex Only", "Group Sex", "BDSM", "POV", "Insult", "Private Cam"
        ]
        
        categories = {}
        
        for video in videos:
            for cat in video.get('categories', []):
                categories[cat] = categories.get(cat, 0) + 1
        
        # Build result with standard categories first, then others
        result = []
        
        # Add standard categories in order if they exist
        for cat_name in standard_categories:
            if cat_name in categories:
                result.append(Category(
                    name=cat_name,
                    video_count=categories[cat_name],
                    thumbnail_url=category_image_map.get(cat_name, '/placeholder.jpg')
                ))
        
        # Add remaining categories sorted by count (use placeholder for unknown categories)
        remaining = [(name, count) for name, count in categories.items() if name not in standard_categories]
        for name, count in sorted(remaining, key=lambda x: x[1], reverse=True):
            result.append(Category(
                name=name,
                video_count=count,
                thumbnail_url=category_image_map.get(name, '/placeholder.jpg')
            ))
        
        return result
    
    def get_studios(self) -> List[Studio]:
        """Get all studios with counts"""
        videos = self._load_videos()
        studios = {}
        
        for video in videos:
            studio = video.get('studio')
            if studio:
                studios[studio] = studios.get(studio, 0) + 1
        
        return [
            Studio(name=name, video_count=count)
            for name, count in sorted(studios.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def get_cast(self) -> List[Cast]:
        """Get all cast members with counts and images"""
        videos = self._load_videos()
        cast_dict = {}
        
        for video in videos:
            cast_images = video.get('cast_images', {})
            # Use models if cast is not available
            cast_list = video.get('cast', video.get('models', []))
            for actress in cast_list:
                if actress not in cast_dict:
                    cast_dict[actress] = {
                        "name": actress,
                        "video_count": 0,
                        "image_url": cast_images.get(actress)
                    }
                cast_dict[actress]["video_count"] += 1
        
        return [
            Cast(**data)
            for data in sorted(cast_dict.values(), key=lambda x: x["video_count"], reverse=True)
        ]
    
    def search_videos(self, query: str, limit: int = 20) -> List[VideoListItem]:
        """Search videos by title or code"""
        videos = self._load_videos()
        q_lower = query.lower()
        
        results = [v for v in videos if 
                   q_lower in v.get('title', '').lower() or 
                   q_lower in v.get('code', '').lower()]
        
        # Normalize results
        normalized = [self._normalize_video(v) for v in results[:limit]]
        
        return [VideoListItem(**v) for v in normalized]

# Singleton instance
video_service = VideoService()
