import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';

export default function Footer() {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="w-full border-t border-border/50 bg-card/30 backdrop-blur-sm mt-20">
            <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    {/* Brand Section */}
                    <div className="col-span-1 md:col-span-2">
                        <Link to="/" className="flex items-center group w-fit mb-4 transition-all duration-300 hover:scale-105 hover:-translate-y-0.5 relative">
                            <img 
                                src="/logo-icon.svg" 
                                alt="Javcore" 
                                className="w-[20px] h-[25px] translate-y-[4px]" 
                            />
                            <span className="text-2xl font-light text-foreground dark:text-white -ml-[1px] relative tracking-wide">
                                avcore
                                <span className="absolute -bottom-0.5 left-0 w-full h-0.5 bg-gradient-to-r from-primary via-primary to-transparent"></span>
                            </span>
                            <div className="absolute -inset-2 bg-gradient-to-r from-primary/0 via-primary/20 to-primary/0 rounded-lg opacity-0 group-hover:opacity-100 blur-sm transition-opacity duration-300"></div>
                        </Link>
                        <p className="text-sm text-muted-foreground dark:text-white/60 max-w-md mb-4">
                            Your premium destination for high-quality adult entertainment. 
                            Discover thousands of videos from top studios and actresses.
                        </p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground dark:text-white/60">
                            <span>Made with</span>
                            <Heart size={14} className="text-primary fill-primary animate-pulse" />
                            <span>by Javcore Team</span>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="font-semibold text-foreground dark:text-white mb-4">Explore</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <Link to="/" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    Home
                                </Link>
                            </li>
                            <li>
                                <Link to="/categories" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    Categories
                                </Link>
                            </li>
                            <li>
                                <Link to="/studios" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    Studios
                                </Link>
                            </li>
                            <li>
                                <Link to="/actresses" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    Actresses
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Legal Links */}
                    <div>
                        <h3 className="font-semibold text-foreground dark:text-white mb-4">Legal</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <a href="#" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    Terms of Service
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    Privacy Policy
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    DMCA
                                </a>
                            </li>
                            <li>
                                <a href="#" className="text-muted-foreground dark:text-white/70 hover:text-primary dark:hover:text-primary transition-colors">
                                    Contact Us
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="pt-8 border-t border-border/50">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-muted-foreground dark:text-white/60">
                        <p>© {currentYear} Javcore. All rights reserved.</p>
                        <p className="text-xs">
                            This site is for adults only. You must be 18+ to access this content.
                        </p>
                    </div>
                </div>
            </div>
        </footer>
    );
}
