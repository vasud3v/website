from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json
from app.core.config import settings

router = APIRouter()

@router.get("/{code}/direct-url")
async def get_preview_direct_url(code: str):
    """Get direct preview video URL from Internet Archive or other sources"""
    try:
        # Load video data using the same path as video_service
        with open(settings.DATABASE_PATH, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        # Find the video
        video = next((v for v in videos if v.get('code') == code), None)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check for Internet Archive preview first (best option - unlimited free)
        preview_ia = video.get('preview_ia', {})
        if preview_ia.get('direct_url'):
            return JSONResponse({
                "direct_url": preview_ia['direct_url'],
                "has_preview": True,
                "source": "internet_archive",
                "details_url": preview_ia.get('details_url')
            })
        
        # Check for Backblaze B2 preview
        preview_b2 = video.get('preview_b2', {})
        if preview_b2.get('direct_url'):
            return JSONResponse({
                "direct_url": preview_b2['direct_url'],
                "has_preview": True,
                "source": "backblaze_b2"
            })
        
        # No preview available
        return JSONResponse({"direct_url": None, "has_preview": False})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "direct_url": None, 
            "has_preview": False, 
            "error": str(e)
        })
