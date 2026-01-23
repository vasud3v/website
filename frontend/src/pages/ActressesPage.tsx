import { useCachedApi } from '../hooks/useApi';
import { api, proxyImageUrl } from '../lib/api';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ActressesPage() {
    const { data, loading, error } = useCachedApi(
        () => api.getAllCastWithImagesDirect(),
        { cacheKey: 'cast-all', ttl: 300000 }
    );

    if (loading) return <LoadingSpinner />;
    if (error) return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <img src="/logo-icon.svg" alt="Javcore" className="w-12 h-16 opacity-50" />
            <p className="text-center text-destructive">Error: {error}</p>
        </div>
    );
    if (!data || data.length === 0) return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <img src="/logo-icon.svg" alt="Javcore" className="w-12 h-16 opacity-50" />
            <p className="text-center text-muted-foreground">No actresses found</p>
        </div>
    );

    return (
        <div className="w-full max-w-[1280px] mx-auto px-4 py-6">
            <h1 className="text-2xl font-bold mb-6 text-foreground dark:text-white">Actresses</h1>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {data.map((actress) => (
                    <Link
                        key={actress.name}
                        to={`/actress/${encodeURIComponent(actress.name)}`}
                        className="group"
                    >
                        <div className="aspect-square rounded-lg overflow-hidden bg-card mb-2 border border-border/50">
                            {actress.image_url ? (
                                <img
                                    src={proxyImageUrl(actress.image_url)}
                                    alt={actress.name}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                                    loading="lazy"
                                    onError={(e) => {
                                        const target = e.target as HTMLImageElement;
                                        target.style.display = 'none';
                                        target.parentElement!.innerHTML = '<div class="w-full h-full flex items-center justify-center text-muted-foreground dark:text-white/60">No Image</div>';
                                    }}
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-muted-foreground dark:text-white/60">
                                    No Image
                                </div>
                            )}
                        </div>
                        <h3 className="font-semibold text-sm line-clamp-2 text-foreground dark:text-white">{actress.name}</h3>
                        <p className="text-xs text-muted-foreground dark:text-white/60">{actress.video_count} videos</p>
                    </Link>
                ))}
            </div>
        </div>
    );
}
