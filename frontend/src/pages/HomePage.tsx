import { useCachedApi } from '../hooks/useApi';
import { api } from '../lib/api';
import { getUserId } from '../lib/user';
import VideoGrid from '../components/VideoGrid';
import LoadingSpinner from '../components/LoadingSpinner';

export default function HomePage() {
    const userId = getUserId();
    const { data, loading, error } = useCachedApi(
        () => api.getHomeFeedDirect(userId),
        { cacheKey: `home-feed:${userId}`, ttl: 120000 }
    );

    if (loading) return <LoadingSpinner />;
    if (error) return <div className="text-center text-red-500 mt-20">Error: {error}</div>;
    if (!data) return null;

    return (
        <div className="space-y-12 pb-12">
            {data.featured?.length > 0 && (
                <section>
                    <h2 className="text-2xl font-bold mb-6 text-zinc-900 dark:text-white">Featured</h2>
                    <VideoGrid videos={data.featured} />
                </section>
            )}
            
            {data.trending?.length > 0 && (
                <section>
                    <h2 className="text-2xl font-bold mb-6 text-zinc-900 dark:text-white">Trending</h2>
                    <VideoGrid videos={data.trending} />
                </section>
            )}
            
            {data.popular?.length > 0 && (
                <section>
                    <h2 className="text-2xl font-bold mb-6 text-zinc-900 dark:text-white">Popular</h2>
                    <VideoGrid videos={data.popular} />
                </section>
            )}
            
            {data.top_rated?.length > 0 && (
                <section>
                    <h2 className="text-2xl font-bold mb-6 text-zinc-900 dark:text-white">Top Rated</h2>
                    <VideoGrid videos={data.top_rated} />
                </section>
            )}
            
            {data.new_releases?.length > 0 && (
                <section>
                    <h2 className="text-2xl font-bold mb-6 text-zinc-900 dark:text-white">New Releases</h2>
                    <VideoGrid videos={data.new_releases} />
                </section>
            )}
            
            {data.classics?.length > 0 && (
                <section>
                    <h2 className="text-2xl font-bold mb-6 text-zinc-900 dark:text-white">Classics</h2>
                    <VideoGrid videos={data.classics} />
                </section>
            )}
        </div>
    );
}
