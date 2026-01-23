import { useCachedApi } from '../hooks/useApi';
import { api } from '../lib/api';
import { getUserId } from '../lib/user';
import VideoCard from '../components/VideoCard';
import OwlCarousel from '../components/OwlCarousel';
import { ChevronRight } from 'lucide-react';

// Full Video Section (Recent Update, Hot Videos, Being Watched)
function VideoSection({ 
    title, 
    subtitle, 
    videos, 
    loading,
    moreLink = '#'
}: { 
    title: string; 
    subtitle: string; 
    videos: any[]; 
    loading: boolean;
    moreLink?: string;
}) {
    return (
        <section className="pb-3 pb-e-lg-40">
            {/* title-with-more */}
            <div className="title-with-more">
                {/* title-box */}
                <div className="title-box">
                    <h6 className="sub-title inactive-color">
                        {subtitle}
                    </h6>
                    <h2 className="h3-md">
                        {title}
                    </h2>
                </div>
                {/* more */}
                <div className="more">
                    <a href={moreLink}>
                        More
                        <ChevronRight className="pl-1" height="20" width="20" />
                    </a>
                </div>
            </div>

            {/* jable-carousel with gutter-20 */}
            <div className="jable-carousel" data-dots="yes" data-items-responsive="0:2|576:3|992:4">
                <div className="gutter-20">
                    {loading ? (
                        <div className="row">
                            {[...Array(8)].map((_, i) => (
                                <div key={i} className="col-6 col-sm-4 col-lg-3">
                                    <div className="item">
                                        <div className="video-img-box mb-e-20">
                                            <div className="img-box">
                                                <a style={{ display: 'block', paddingBottom: '56.25%', background: '#27272a' }} />
                                            </div>
                                            <div className="detail">
                                                <div style={{ height: '1rem', background: '#3f3f46', borderRadius: '0.25rem', marginBottom: '0.5rem' }} />
                                                <div style={{ height: '0.75rem', background: '#3f3f46', borderRadius: '0.25rem', width: '50%' }} />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : videos.length > 0 ? (
                        <OwlCarousel key={`carousel-${videos.length}`}>
                            {/* Each carousel item contains 2 videos stacked vertically - exact Jable.tv structure */}
                            {Array.from({ length: Math.ceil(videos.length / 2) }, (_, i) => {
                                const video1 = videos[i * 2];
                                const video2 = videos[i * 2 + 1];
                                return (
                                    <div key={`item-${i}`} className="item">
                                        {video1 && <VideoCard video={video1} />}
                                        {video2 && <VideoCard video={video2} />}
                                    </div>
                                );
                            })}
                        </OwlCarousel>
                    ) : (
                        <div className="text-center py-8 text-zinc-500">
                            No videos available
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}

// Cover Section (New Release) - 6 columns, portrait covers only
function CoverSection({ 
    title, 
    subtitle, 
    videos, 
    loading,
    moreLink = '#'
}: { 
    title: string; 
    subtitle: string; 
    videos: any[]; 
    loading: boolean;
    moreLink?: string;
}) {
    return (
        <section className="pb-3 pb-e-lg-40">
            {/* title-with-more */}
            <div className="title-with-more">
                {/* title-box */}
                <div className="title-box">
                    <h6 className="sub-title inactive-color">
                        {subtitle}
                    </h6>
                    <h2 className="h3-md">
                        {title}
                    </h2>
                </div>
                {/* more */}
                <div className="more">
                    <a href={moreLink}>
                        More
                        <ChevronRight className="pl-1" height="20" width="20" />
                    </a>
                </div>
            </div>

            {/* jable-carousel with gutter-20 */}
            <div className="jable-carousel" data-items-responsive="0:3|576:4|992:6">
                <div className="gutter-20">
                    <div className="owl-carousel owl-loaded owl-theme-jable">
                        <div className="row">
                            {loading ? (
                                [...Array(6)].map((_, i) => (
                                    <div key={i} className="col-2">
                                        <div className="item">
                                            <div className="video-img-box">
                                                <div className="img-box cover-half">
                                                    <a style={{ display: 'block', paddingBottom: '142%', background: '#27272a' }} />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                videos.slice(0, 6).map((video) => (
                                    <div key={video.code} className="col-2">
                                        <div className="item">
                                            {/* video-img-box */}
                                            <div className="video-img-box">
                                                {/* img-box cover-half */}
                                                <div className="img-box cover-half">
                                                    <a 
                                                        href={`/video/${video.code}`}
                                                        style={{
                                                            backgroundImage: `url('${video.thumbnail_url || '/placeholder.jpg'}')`
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default function HomePage() {
    const userId = getUserId();
    
    // Fetch home feed with all videos (no limit)
    const { data, loading, error } = useCachedApi(
        () => api.getHomeFeedDirect(userId),
        { cacheKey: `home-feed:${userId}`, ttl: 120000 }
    );

    // Fetch additional videos for each section with larger page sizes
    const { data: trendingData } = useCachedApi(
        () => api.getTrendingVideos(1, 100),
        { cacheKey: 'trending:all', ttl: 120000 }
    );

    const { data: popularData } = useCachedApi(
        () => api.getPopularVideos(1, 100),
        { cacheKey: 'popular:all', ttl: 120000 }
    );

    // Fetch categories
    const { data: categoriesData } = useCachedApi(
        () => api.getCategories(),
        { cacheKey: 'categories:all', ttl: 300000 }
    );

    if (error) return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
            <img src="/logo-icon.svg" alt="Javcore" className="w-12 h-16 opacity-50" />
            <p className="text-center text-destructive">Error: {error}</p>
        </div>
    );

    const newReleases = data?.new_releases || [];
    const categories = categoriesData || [];
    const trendingVideos = trendingData?.items || [];
    const popularVideos = popularData?.items || [];

    // Debug logging
    console.log('HomePage data:', {
        newReleases: newReleases.length,
        categories: categories.length,
        trendingVideos: trendingVideos.length,
        popularVideos: popularVideos.length,
        loading,
        error
    });

    return (
        <div className="container max-w-[1140px] mx-auto px-4">
            {/* 1. Recent Update Section - Show ALL new releases */}
            <VideoSection
                subtitle="Fresh"
                title="Recent Update"
                videos={newReleases}
                loading={loading}
                moreLink="/latest-updates"
            />

            {/* 2. Ad Section */}
            <section className="d-flex justify-content-center pb-3 pb-e-lg-40 text-center">
                <div className="ad-container">
                    Advertisement
                </div>
            </section>

            {/* 3. New Release Section - Show ALL new releases */}
            <CoverSection
                subtitle="Just Baked"
                title="New Release"
                videos={newReleases}
                loading={loading}
                moreLink="/new-release"
            />

            <section className="pb-3 pb-e-lg-40">
                <div className="row">
                    <div className="col-lg-7 pb-3 pb-md-0">
                        <div className="title-with-more">
                            <div className="title-box">
                                <h6 className="sub-title inactive-color">Choice</h6>
                                <h2 className="h3-md">Category</h2>
                            </div>
                            <div className="more">
                                <a href="/categories">
                                    More
                                    <svg className="pl-1" height="20" width="20"><use xlinkHref="#icon-arrow-right"></use></svg>
                                </a>
                            </div>
                        </div>
                        <div className="row gutter-20">
                            {categories.slice(0, 10).map((category: any) => (
                                <div key={category.name} className="col-6">
                                    <div className="horizontal-img-box mb-3">
                                        <a href={`/category/${encodeURIComponent(category.name)}`}>
                                            <div className="media">
                                                <img 
                                                    className="rounded" 
                                                    src={category.thumbnail_url || '/placeholder.jpg'} 
                                                    width="50"
                                                    alt={category.name}
                                                />
                                                <div className="detail">
                                                    <h6 className="title">{category.name}</h6>
                                                    <span>{category.video_count || 0} videos</span>
                                                </div>
                                            </div>
                                        </a>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="col-lg-5 d-none d-lg-block">
                        <div className="title-with-more">
                            <div className="title-box">
                                <h6 className="sub-title inactive-color">On Focus</h6>
                                <h2 className="h3-md">Collections</h2>
                            </div>
                        </div>
                        <div className="row gutter-20">
                            <div className="col-6">
                                <a className="card bg-pink text-light" href="/tags/black-pantyhose">
                                    <img className="overlay-image" src="https://assets-cdn.jable.tv/assets/images/card-overlay.png" />
                                    <div className="card-body with-icon-title">
                                        <div className="icon-title">
                                            <svg height="24" width="24"><use xlinkHref="#icon-fire"></use></svg>
                                        </div>
                                        <div>
                                            <h4 className="mb-3"># Black Pantyhose</h4>
                                            <span className="text-white">A symbol of sexiness, a temptation no man can resist.</span>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <div className="col-6">
                                <a className="card bg-gray text-light" href="/tags/school-uniform">
                                    <img className="overlay-image" src="https://assets-cdn.jable.tv/assets/images/card-overlay.png" />
                                    <div className="card-body with-icon-title">
                                        <div className="icon-title">
                                            <svg height="24" width="24"><use xlinkHref="#icon-like"></use></svg>
                                        </div>
                                        <div>
                                            <h4 className="mb-3"># School Uniform</h4>
                                            <span className="text-white">The youthful memories that flutter the heart upon recollection.</span>
                                        </div>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* 5. Ad Section */}
            <section className="d-flex justify-content-center pb-3 pb-e-lg-40 text-center">
                <div className="ad-container">
                    Advertisement
                </div>
            </section>

            {/* 6. Hot Videos Section - Show ALL trending videos */}
            <VideoSection
                subtitle="This Week"
                title="Hot Videos"
                videos={trendingVideos}
                loading={loading}
                moreLink="/hot"
            />

            {/* 7. Being Watched Section - Show ALL popular videos */}
            <VideoSection
                subtitle="Trending"
                title="Being Watched"
                videos={popularVideos}
                loading={loading}
                moreLink="/trending"
            />
        </div>
    );
}
