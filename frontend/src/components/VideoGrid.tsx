import { memo } from 'react';
import type { VideoListItem } from '../lib/api';
import VideoCard from './VideoCard';
import { VideoGridSkeleton } from './Skeleton';

interface VideoGridProps {
  videos: VideoListItem[];
  loading?: boolean;
  onVideoClick?: (code: string) => void;
  columns?: 'auto' | 4 | 5 | 6 | 7;
}

const VideoGrid = memo(function VideoGrid({ 
  videos, 
  loading, 
  onVideoClick, 
  columns = 'auto'
}: VideoGridProps) {
  if (loading) {
    return <VideoGridSkeleton />;
  }

  if (videos.length === 0) {
    return (
      <div className="text-center py-12 text-zinc-500">
        No videos found
      </div>
    );
  }

  // Grid configurations for landscape videos
  const gridClasses = {
    'auto': 'grid grid-cols-4 gap-4',
    4: 'grid grid-cols-4 gap-4',
    5: 'grid grid-cols-4 gap-4',
    6: 'grid grid-cols-4 gap-4',
    7: 'grid grid-cols-4 gap-4'
  };

  return (
    <div className={gridClasses[columns]}>
      {videos.map((video) => (
        <VideoCard 
          key={video.code} 
          video={video} 
          onClick={onVideoClick}
        />
      ))}
    </div>
  );
});

export default VideoGrid;
