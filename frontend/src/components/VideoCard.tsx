/**
 * Video Card matching jable.tv exact structure
 */

import { useState, memo, useCallback, useMemo, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Heart } from 'lucide-react';
import type { VideoListItem } from '../lib/api';
import { proxyImageUrl } from '../lib/api';

interface VideoCardProps {
  video: VideoListItem;
  onClick?: (code: string) => void;
}

const formatViews = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
};

const isPlaceholderImage = (url: string | null | undefined): boolean => {
  if (!url) return true;
  const lowerUrl = url.toLowerCase();
  return ['nowprinting', 'now_printing', 'noimage', 'no_image', 'placeholder', 'coming_soon', 'comingsoon']
    .some(pattern => lowerUrl.includes(pattern));
};

const VideoCard = memo(function VideoCard({ 
  video, 
  onClick
}: VideoCardProps) {
  const navigate = useNavigate();
  const [imageError, setImageError] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewLoaded, setPreviewLoaded] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const hasValidThumbnail = useMemo(
    () => {
      if (!video.thumbnail_url) return false;
      if (imageError) return false;
      if (isPlaceholderImage(video.thumbnail_url)) return false;
      try {
        const url = video.thumbnail_url.trim();
        return url.length > 0 && (url.startsWith('http') || url.startsWith('/'));
      } catch {
        return false;
      }
    },
    [video.thumbnail_url, imageError]
  );

  const thumbnailUrl = useMemo(
    () => {
      if (!hasValidThumbnail) return null;
      return proxyImageUrl(video.thumbnail_url);
    },
    [hasValidThumbnail, video.thumbnail_url]
  );

  const formattedViews = useMemo(() => formatViews(video.views || 0), [video.views]);
  const formattedLikes = useMemo(() => formatViews(video.like_count || 0), [video.like_count]);

  const handleClick = useCallback(() => {
    if (onClick) {
      onClick(video.code);
    } else {
      navigate(`/video/${encodeURIComponent(video.code)}`);
    }
  }, [onClick, video.code, navigate]);

  const handleImageError = useCallback(() => {
    setImageError(true);
  }, []);

  const handleMouseEnter = useCallback(() => {
    if (video.preview_video_url) {
      hoverTimeoutRef.current = setTimeout(() => {
        setShowPreview(true);
      }, 500); // 500ms delay before showing preview
    }
  }, [video.preview_video_url]);

  const handleMouseLeave = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
    setShowPreview(false);
    setPreviewLoaded(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  }, []);

  useEffect(() => {
    if (showPreview && videoRef.current && !previewLoaded) {
      videoRef.current.play().catch(() => {
        // Autoplay failed, ignore
      });
    }
  }, [showPreview, previewLoaded]);

  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="video-img-box mb-e-20">
      {/* img-box */}
      <div 
        className="img-box"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <a 
          onClick={(e) => { e.preventDefault(); handleClick(); }}
          className="cursor-pointer"
        >
          {thumbnailUrl && !imageError ? (
            <img
              src={thumbnailUrl}
              alt={video.title}
              onError={handleImageError}
              loading="lazy"
              style={{
                opacity: showPreview ? 0 : 1,
                transition: 'opacity 0.3s ease'
              }}
            />
          ) : (
            <div style={{ 
              position: 'absolute', 
              inset: 0, 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center', 
              justifyContent: 'center', 
              background: 'linear-gradient(135deg, #27272a 0%, #18181b 100%)',
              gap: '0.5rem',
              opacity: showPreview ? 0 : 1,
              transition: 'opacity 0.3s ease'
            }}>
              <svg 
                width="48" 
                height="48" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="1.5"
                style={{ color: '#52525b', opacity: 0.5 }}
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              <span style={{ fontSize: '0.75rem', color: '#71717a', fontWeight: 500 }}>
                {video.code}
              </span>
            </div>
          )}

          {/* Video Preview */}
          {video.preview_video_url && showPreview && (
            <>
              {!previewLoaded && (
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  zIndex: 2
                }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    border: '3px solid rgba(255, 255, 255, 0.3)',
                    borderTop: '3px solid white',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite'
                  }} />
                </div>
              )}
              <video
                ref={videoRef}
                src={video.preview_video_url}
                loop
                muted
                playsInline
                onLoadedData={() => setPreviewLoaded(true)}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  opacity: previewLoaded ? 1 : 0,
                  transition: 'opacity 0.3s ease',
                  zIndex: 1
                }}
              />
            </>
          )}

          {/* absolute-bottom-right - Duration */}
          {video.duration && (
            <div className="absolute-bottom-right">
              <span className="label">
                {video.duration}
              </span>
            </div>
          )}

          {/* absolute-bottom-left - Favorite button */}
          <div className="absolute-bottom-left">
            <span className="action hover-state d-none d-sm-flex">
              <Heart height="15" width="15" />
            </span>
          </div>
        </a>
      </div>

      {/* detail */}
      <div className="detail">
        <h6 className="title">
          <a 
            onClick={(e) => { e.preventDefault(); handleClick(); }}
          >
            {video.title}
          </a>
        </h6>
        <p className="sub-title">
          <Eye className="mr-1" height="15" width="15" />
          {formattedViews}
          <Heart className="ml-3 mr-1" height="13" width="13" />
          {formattedLikes}
        </p>
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
  return (
    prevProps.video.code === nextProps.video.code &&
    prevProps.video.thumbnail_url === nextProps.video.thumbnail_url &&
    prevProps.video.views === nextProps.video.views &&
    prevProps.video.like_count === nextProps.video.like_count
  );
});

export default VideoCard;
