
import { Link } from 'react-router-dom';
import { Search, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-transparent backdrop-blur-sm border-b border-white/10">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="text-2xl font-bold bg-gradient-to-r from-pink-500 to-red-500 bg-clip-text text-transparent">
                        JAVCore
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center space-x-8">
                        <Link to="/" className="text-gray-300 hover:text-white transition-colors">Home</Link>
                        <Link to="/categories" className="text-gray-300 hover:text-white transition-colors">Categories</Link>
                        <Link to="/studios" className="text-gray-300 hover:text-white transition-colors">Studios</Link>
                        <Link to="/actresses" className="text-gray-300 hover:text-white transition-colors">Actresses</Link>
                    </div>

                    {/* Search and Mobile Menu Button */}
                    <div className="flex items-center gap-4">
                        <button className="p-2 text-gray-400 hover:text-white transition-colors">
                            <Search size={20} />
                        </button>
                        <button
                            className="md:hidden p-2 text-gray-400 hover:text-white transition-colors"
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                        >
                            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu */}
            {isMenuOpen && (
                <div className="md:hidden bg-black/95 backdrop-blur-xl border-t border-white/10">
                    <div className="flex flex-col p-4 space-y-4">
                        <Link to="/" className="text-gray-300 hover:text-white px-2 py-1">Home</Link>
                        <Link to="/categories" className="text-gray-300 hover:text-white px-2 py-1">Categories</Link>
                        <Link to="/studios" className="text-gray-300 hover:text-white px-2 py-1">Studios</Link>
                        <Link to="/actresses" className="text-gray-300 hover:text-white px-2 py-1">Actresses</Link>
                    </div>
                </div>
            )}
        </nav>
    );
}
