import { useCachedApi } from '../hooks/useApi';
import { api } from '../lib/api';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';

export default function CategoriesPage() {
    const { data, loading, error } = useCachedApi(
        () => api.getCategories(),
        { cacheKey: 'categories', ttl: 300000 }
    );

    if (loading) return <LoadingSpinner />;
    if (error) return <div className="text-center text-red-500 mt-20">Error: {error}</div>;
    if (!data) return null;

    return (
        <div>
            <h1 className="text-3xl font-bold mb-8">Categories</h1>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {data.map((category) => (
                    <Link
                        key={category.name}
                        to={`/category/${encodeURIComponent(category.name)}`}
                        className="p-6 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
                    >
                        <h3 className="font-semibold mb-2">{category.name}</h3>
                        <p className="text-sm text-gray-400">{category.video_count} videos</p>
                    </Link>
                ))}
            </div>
        </div>
    );
}
