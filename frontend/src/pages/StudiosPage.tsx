import { useCachedApi } from '../hooks/useApi';
import { api } from '../lib/api';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';

export default function StudiosPage() {
    const { data, loading, error } = useCachedApi(
        () => api.getStudios(),
        { cacheKey: 'studios', ttl: 300000 }
    );

    if (loading) return <LoadingSpinner />;
    if (error) return <div className="text-center text-red-500 mt-20">Error: {error}</div>;
    if (!data) return null;

    return (
        <div>
            <h1 className="text-3xl font-bold mb-8 text-zinc-900 dark:text-white">Studios</h1>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {data.map((studio) => (
                    <Link
                        key={studio.name}
                        to={`/studio/${encodeURIComponent(studio.name)}`}
                        className="p-6 bg-zinc-200 dark:bg-gray-800 rounded-lg hover:bg-zinc-300 dark:hover:bg-gray-700 transition-colors"
                    >
                        <h3 className="font-semibold mb-2 text-zinc-900 dark:text-white">{studio.name}</h3>
                        <p className="text-sm text-zinc-600 dark:text-gray-400">{studio.video_count} videos</p>
                    </Link>
                ))}
            </div>
        </div>
    );
}
