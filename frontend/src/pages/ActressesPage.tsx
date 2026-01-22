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
    if (error) return <div className="text-center text-red-500 mt-20">Error: {error}</div>;
    if (!data) return null;

    return (
        <div>
            <h1 className="text-3xl font-bold mb-8 text-zinc-900 dark:text-white">Actresses</h1>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {data.map((actress) => (
                    <Link
                        key={actress.name}
                        to={`/actress/${encodeURIComponent(actress.name)}`}
                        className="group"
                    >
                        <div className="aspect-square rounded-lg overflow-hidden bg-zinc-200 dark:bg-gray-800 mb-2">
                            {actress.image_url ? (
                                <img
                                    src={proxyImageUrl(actress.image_url)}
                                    alt={actress.name}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                                    loading="lazy"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-zinc-500 dark:text-gray-500">
                                    No Image
                                </div>
                            )}
                        </div>
                        <h3 className="font-semibold text-sm line-clamp-2 text-zinc-900 dark:text-white">{actress.name}</h3>
                        <p className="text-xs text-zinc-600 dark:text-gray-400">{actress.video_count} videos</p>
                    </Link>
                ))}
            </div>
        </div>
    );
}
