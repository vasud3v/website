import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import SvgSprite from './components/SvgSprite';
import { ErrorBoundary } from './components/ErrorBoundary';
import HomePage from './pages/HomePage';
import CategoriesPage from './pages/CategoriesPage';
import StudiosPage from './pages/StudiosPage';
import ActressesPage from './pages/ActressesPage';
import VideoDetailPage from './pages/VideoDetailPage';

function App() {
    return (
        <ErrorBoundary>
            <Router>
                <SvgSprite />
                <div className="min-h-screen bg-background text-foreground transition-colors duration-300 flex flex-col">
                    <Navbar />
                    <main className="pt-20 pb-8 flex-1">
                        <Routes>
                            <Route path="/" element={<HomePage />} />
                            <Route path="/categories" element={<CategoriesPage />} />
                            <Route path="/studios" element={<StudiosPage />} />
                            <Route path="/actresses" element={<ActressesPage />} />
                            <Route path="/video/:code" element={<VideoDetailPage />} />
                        </Routes>
                    </main>
                    <Footer />
                </div>
            </Router>
        </ErrorBoundary>
    );
}

export default App;
