import { Link } from 'react-router-dom';
import { VideoListItem, proxyImageUrl } from '../lib/api';
import { Star, Eye } from 'lucide-react';

interface VideoGridProps {
    videos: VideoListItem[];
}

export default function VideoGrid({ videos }: VideoGridProps) {
    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {videos.map((video) => (
                <Link
                    key={video.code}
                    to={`/video/${video.code}`}
                    className="group relative overflow-hidden rounded-lg bg-zinc-200 dark:bg-gray-800 hover:ring-2 hover:ring-pink-500 transition-all"
                >
                    <div className="aspect-[2/3] relative">
                        <img
                            src={proxyImageUrl(video.thumbnail_url)}
                            alt={video.title}
                            className="w-full h-full object-cover"
                            loading="lazy"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    
                    <div className="p-3">
                        <h3 className="font-semibold text-sm line-clamp-2 mb-1 text-zinc-900 dark:text-white">{video.title}</h3>
                        <p className="text-xs text-zinc-500 dark:text-gray-400 mb-2">{video.code}</p>
                        
                        <div className="flex items-center justify-between text-xs text-zinc-500 dark:text-gray-400">
                            <div className="flex items-center gap-1">
                                <Star size={12} className="text-yellow-500" />
                                <span>{video.rating_avg?.toFixed(1) || 'N/A'}</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <Eye size={12} />
                                <span>{video.views || 0}</span>
                            </div>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    );
}
