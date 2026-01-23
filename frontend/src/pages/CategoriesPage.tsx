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
    if (error) return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <img src="/logo-icon.svg" alt="Javcore" className="w-12 h-16 opacity-50" />
            <p className="text-center text-destructive">Error: {error}</p>
        </div>
    );
    if (!data || data.length === 0) return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <img src="/logo-icon.svg" alt="Javcore" className="w-12 h-16 opacity-50" />
            <p className="text-center text-muted-foreground">No categories found</p>
        </div>
    );

    return (
        <div className="w-full max-w-[1280px] mx-auto px-4 py-6">
            <h1 className="text-2xl font-bold mb-6 text-foreground dark:text-white">Categories</h1>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {data.map((category) => (
                    <Link
                        key={category.name}
                        to={`/category/${encodeURIComponent(category.name)}`}
                        className="p-6 bg-card rounded-lg hover:bg-accent transition-colors border border-border/50"
                    >
                        <h3 className="font-semibold mb-2 text-card-foreground dark:text-white">{category.name}</h3>
                        <p className="text-sm text-muted-foreground dark:text-white/60">{category.video_count} videos</p>
                    </Link>
                ))}
            </div>
        </div>
    );
}
