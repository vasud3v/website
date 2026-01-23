import { Link, useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useState } from 'react';
import { useTheme } from '../context/ThemeContext';

export default function Navbar() {
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const { theme, toggleTheme } = useTheme();
    const navigate = useNavigate();

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const trimmed = searchQuery.trim();
        if (trimmed) {
            navigate(`/search?q=${encodeURIComponent(trimmed)}`);
            setSearchQuery(''); // Clear search after navigation
        }
    };

    const isDarkMode = theme === 'dark';

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300 bg-transparent">
            <div className="flex items-center h-14 px-6 max-w-[1920px] mx-auto">
                {/* Left Section - Menu & Logo */}
                <div className="flex items-center gap-4 w-64">
                    <button className="p-2 hover:bg-accent rounded-lg transition-all duration-200 active:scale-95 group">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-foreground group-hover:text-primary transition-colors">
                            <line x1="3" y1="12" x2="21" y2="12"></line>
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <line x1="3" y1="18" x2="21" y2="18"></line>
                        </svg>
                    </button>
                    <Link to="/" className="flex items-center group relative transition-all duration-300 hover:scale-105 hover:-translate-y-0.5">
                        <img src="/logo-icon.svg" alt="Javcore" className="w-[20px] h-[25px] translate-y-[4px]" />
                        <span className="text-xl font-light text-foreground dark:text-white -ml-[1px] relative tracking-wide">
                            avcore
                            <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-gradient-to-r from-primary via-primary to-transparent"></span>
                        </span>
                        <div className="absolute -inset-2 bg-gradient-to-r from-primary/0 via-primary/20 to-primary/0 rounded-lg opacity-0 group-hover:opacity-100 blur-sm transition-opacity duration-300"></div>
                    </Link>
                </div>

                {/* Center Section - Navigation Icons & Search */}
                <div className="flex items-center gap-2 flex-1 justify-center">
                    {/* Home Icon */}
                    <Link 
                        to="/" 
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group relative backdrop-blur-sm"
                        title="Home"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/70 dark:text-white group-hover:text-foreground dark:group-hover:text-white transition-all duration-200 group-hover:scale-110 drop-shadow-lg">
                            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                            <polyline points="9 22 9 12 15 12 15 22"></polyline>
                        </svg>
                        <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-0.5 bg-gradient-to-r from-transparent via-foreground dark:via-white to-transparent group-hover:w-8 transition-all duration-300 shadow-lg shadow-foreground/50 dark:shadow-white/50"></span>
                    </Link>
                    
                    {/* Grid Icon */}
                    <Link 
                        to="/categories" 
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group relative backdrop-blur-sm"
                        title="Categories"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/70 dark:text-white group-hover:text-foreground dark:group-hover:text-white transition-all duration-200 group-hover:scale-110 drop-shadow-lg">
                            <rect x="3" y="3" width="7" height="7"></rect>
                            <rect x="14" y="3" width="7" height="7"></rect>
                            <rect x="14" y="14" width="7" height="7"></rect>
                            <rect x="3" y="14" width="7" height="7"></rect>
                        </svg>
                        <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-0.5 bg-gradient-to-r from-transparent via-foreground dark:via-white to-transparent group-hover:w-8 transition-all duration-300 shadow-lg shadow-foreground/50 dark:shadow-white/50"></span>
                    </Link>

                    {/* Search Bar */}
                    <form onSubmit={handleSearch} className="relative mx-3 group">
                        <div className={`absolute -inset-0.5 bg-gradient-to-r from-primary to-primary/80 rounded-lg opacity-0 blur transition-opacity duration-300 ${
                            isSearchFocused ? 'opacity-30' : ''
                        }`}></div>
                        <Search 
                            size={16} 
                            strokeWidth={1.5}
                            className={`absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none transition-all duration-200 z-10 drop-shadow-lg ${
                                isSearchFocused ? 'text-primary scale-110' : 'text-foreground/60 dark:text-white/80'
                            }`} 
                        />
                        <input
                            type="text"
                            placeholder="Search "
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onFocus={() => setIsSearchFocused(true)}
                            onBlur={() => setIsSearchFocused(false)}
                            className={`relative w-48 pl-10 pr-4 py-2 bg-input backdrop-blur-sm border rounded-lg text-sm text-foreground placeholder-muted-foreground transition-all duration-300 ${
                                isSearchFocused 
                                    ? 'ring-2 ring-primary/50 border-primary/50 w-64 shadow-lg shadow-primary/20' 
                                    : 'border-border focus:ring-1 focus:ring-ring'
                            }`}
                        />
                    </form>

                    {/* Trending Icon */}
                    <Link 
                        to="/trending" 
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group relative backdrop-blur-sm"
                        title="Trending"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/70 dark:text-white group-hover:text-foreground dark:group-hover:text-white transition-all duration-200 group-hover:scale-110 drop-shadow-lg">
                            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
                            <polyline points="16 7 22 7 22 13"></polyline>
                        </svg>
                        <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-0.5 bg-gradient-to-r from-transparent via-foreground dark:via-white to-transparent group-hover:w-8 transition-all duration-300 shadow-lg shadow-foreground/50 dark:shadow-white/50"></span>
                    </Link>

                    {/* Heart Icon */}
                    <Link 
                        to="/favorites" 
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group relative backdrop-blur-sm"
                        title="Favorites"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/70 dark:text-white group-hover:text-primary transition-all duration-200 group-hover:scale-110 group-hover:fill-primary/30 drop-shadow-lg group-hover:drop-shadow-[0_0_8px_rgba(227,114,168,0.6)]">
                            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                        </svg>
                        <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-0 h-0.5 bg-gradient-to-r from-transparent via-primary to-transparent group-hover:w-8 transition-all duration-300 shadow-lg shadow-primary/50"></span>
                    </Link>
                </div>

                {/* Right Section - More Icons */}
                <div className="flex items-center gap-2 w-64 justify-end">
                    {/* Theme Toggle Icon */}
                    <button 
                        onClick={toggleTheme}
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group active:scale-95 backdrop-blur-sm relative overflow-hidden"
                        title="Toggle Theme"
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-yellow-500/0 via-yellow-500/10 to-yellow-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative w-5 h-5">
                            {/* Sun Icon */}
                            <svg 
                                width="20" 
                                height="20" 
                                viewBox="0 0 24 24" 
                                fill="none" 
                                stroke="currentColor" 
                                strokeWidth="1.5" 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                className={`absolute inset-0 text-foreground/70 group-hover:text-yellow-500 transition-all duration-500 drop-shadow-lg group-hover:drop-shadow-[0_0_12px_rgba(253,224,71,0.8)] ${
                                    isDarkMode ? 'opacity-0 rotate-180 scale-0' : 'opacity-100 rotate-0 scale-100'
                                }`}
                            >
                                <circle cx="12" cy="12" r="4"></circle>
                                <path d="M12 2v2"></path>
                                <path d="M12 20v2"></path>
                                <path d="m4.93 4.93 1.41 1.41"></path>
                                <path d="m17.66 17.66 1.41 1.41"></path>
                                <path d="M2 12h2"></path>
                                <path d="M20 12h2"></path>
                                <path d="m6.34 17.66-1.41 1.41"></path>
                                <path d="m19.07 4.93-1.41 1.41"></path>
                            </svg>
                            {/* Moon Icon */}
                            <svg 
                                width="20" 
                                height="20" 
                                viewBox="0 0 24 24" 
                                fill="none" 
                                stroke="currentColor" 
                                strokeWidth="1.5" 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                className={`absolute inset-0 text-white group-hover:text-blue-400 transition-all duration-500 drop-shadow-lg group-hover:drop-shadow-[0_0_12px_rgba(147,197,253,0.8)] ${
                                    isDarkMode ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-180 scale-0'
                                }`}
                            >
                                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                            </svg>
                        </div>
                    </button>

                    {/* Notifications Icon */}
                    <button 
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group active:scale-95 relative backdrop-blur-sm"
                        title="Notifications"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/70 dark:text-white group-hover:text-foreground dark:group-hover:text-white transition-all duration-200 group-hover:scale-110 group-hover:rotate-12 drop-shadow-lg">
                            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                        </svg>
                        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-background animate-pulse shadow-lg shadow-red-500/50"></span>
                    </button>

                    {/* Bookmarks Icon */}
                    <button 
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group active:scale-95 backdrop-blur-sm"
                        title="Bookmarks"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/70 dark:text-white group-hover:text-foreground dark:group-hover:text-white transition-all duration-200 group-hover:scale-110 group-hover:-translate-y-0.5 drop-shadow-lg">
                            <path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                        </svg>
                    </button>

                    {/* Language Icon */}
                    <button 
                        className="p-2.5 hover:bg-accent rounded-lg transition-all duration-200 group active:scale-95 backdrop-blur-sm"
                        title="Change Language"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/70 dark:text-white group-hover:text-foreground dark:group-hover:text-white transition-all duration-200 group-hover:scale-110 drop-shadow-lg">
                            <path d="m5 8 6 6"></path>
                            <path d="m4 14 6-6 2-3"></path>
                            <path d="M2 5h12"></path>
                            <path d="M7 2h1"></path>
                            <path d="m22 22-5-10-5 10"></path>
                            <path d="M14 18h6"></path>
                        </svg>
                    </button>
                    
                    {/* User Avatar */}
                    <button 
                        className="w-8 h-8 bg-gradient-to-br from-muted to-muted-foreground/30 rounded-full flex items-center justify-center hover:from-accent hover:to-accent-foreground/30 hover:ring-2 hover:ring-ring/30 transition-all duration-300 overflow-hidden group active:scale-95 ml-1 relative shadow-lg"
                        title="Profile"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/0 to-primary/0 group-hover:from-primary/30 group-hover:to-primary/30 transition-all duration-300"></div>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-foreground/80 dark:text-white group-hover:text-foreground dark:group-hover:text-white transition-all duration-200 relative z-10 group-hover:scale-110 drop-shadow-lg">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                    </button>
                </div>
            </div>
        </nav>
    );
}
