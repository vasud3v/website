import { useParams, Link } from 'react-router-dom';
import { useCachedApi } from '../hooks/useApi';
import { api, proxyImageUrl } from '../lib/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { Calendar, Eye, Star, Heart } from 'lucide-react';

export default function VideoDetailPage() {
    const { code } = useParams<{ code: string }>();
    const { data, loading, error } = useCachedApi(
        () => api.getVideo(code!),
        { cacheKey: `video:${code}`, ttl: 300000, skip: !code },
        [code]
    );

    if (!code) return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <img src="/logo-icon.svg" alt="Javcore" className="w-12 h-16 opacity-50" />
            <p className="text-center text-destructive">Invalid video code</p>
        </div>
    );
    if (loading) return <LoadingSpinner />;
    if (error) return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <img src="/logo-icon.svg" alt="Javcore" className="w-12 h-16 opacity-50" />
            <p className="text-center text-destructive">Error: {error}</p>
        </div>
    );
    if (!data) return null;

    return (
        <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-3 gap-8 mb-8">
                <div className="md:col-span-1">
                    <img
                        src={proxyImageUrl(data.cover_url || data.thumbnail_url)}
                        alt={data.title}
                        className="w-full rounded-lg shadow-lg"
                        onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = '/placeholder.jpg';
                        }}
                    />
                </div>
                
                <div className="md:col-span-2">
                    <h1 className="text-3xl font-bold mb-4">{data.title}</h1>
                    <p className="text-xl text-gray-400 mb-6">{data.code}</p>
                    
                    <div className="grid grid-cols-2 gap-4 mb-6">
                        <div className="flex items-center gap-2">
                            <Calendar size={20} className="text-gray-400" />
                            <span>{data.release_date}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Eye size={20} className="text-gray-400" />
                            <span>{data.views} views</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Star size={20} className="text-yellow-500" />
                            <span>{data.rating_avg?.toFixed(1) || 'N/A'} ({data.rating_count} ratings)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Heart size={20} className="text-pink-500" />
                            <span>{data.like_count} likes</span>
                        </div>
                    </div>
                    
                    <div className="space-y-4">
                        <div>
                            <h3 className="font-semibold mb-2">Studio</h3>
                            <Link to={`/studio/${encodeURIComponent(data.studio)}`} className="text-pink-500 hover:underline">
                                {data.studio}
                            </Link>
                        </div>
                        
                        {data.series && (
                            <div>
                                <h3 className="font-semibold mb-2">Series</h3>
                                <p>{data.series}</p>
                            </div>
                        )}
                        
                        {data.description && (
                            <div>
                                <h3 className="font-semibold mb-2">Description</h3>
                                <p className="text-gray-300">{data.description}</p>
                            </div>
                        )}
                        
                        {data.categories?.length > 0 && (
                            <div>
                                <h3 className="font-semibold mb-2">Categories</h3>
                                <div className="flex flex-wrap gap-2">
                                    {data.categories.map((cat) => (
                                        <Link
                                            key={cat}
                                            to={`/category/${encodeURIComponent(cat)}`}
                                            className="px-3 py-1 bg-gray-800 rounded-full text-sm hover:bg-gray-700"
                                        >
                                            {cat}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        )}
                        
                        {data.cast?.length > 0 && (
                            <div>
                                <h3 className="font-semibold mb-2">Cast</h3>
                                <div className="flex flex-wrap gap-2">
                                    {data.cast.map((actress) => (
                                        <Link
                                            key={actress}
                                            to={`/actress/${encodeURIComponent(actress)}`}
                                            className="px-3 py-1 bg-pink-900/30 rounded-full text-sm hover:bg-pink-900/50"
                                        >
                                            {actress}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            
            {data.embed_urls?.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-2xl font-bold mb-4">Watch</h2>
                    <div className="aspect-video bg-black rounded-lg">
                        <iframe
                            src={data.embed_urls[0]}
                            className="w-full h-full rounded-lg"
                            allowFullScreen
                            title={`Watch ${data.title}`}
                            sandbox="allow-scripts allow-same-origin allow-presentation"
                        />
                    </div>
                </div>
            )}
            
            {data.gallery_images?.length > 0 && (
                <div>
                    <h2 className="text-2xl font-bold mb-4">Gallery</h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {data.gallery_images.map((img, idx) => (
                            <img
                                key={idx}
                                src={proxyImageUrl(img)}
                                alt={`Gallery ${idx + 1}`}
                                className="w-full rounded-lg"
                                loading="lazy"
                                onError={(e) => {
                                    const target = e.target as HTMLImageElement;
                                    target.src = '/placeholder.jpg';
                                }}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
