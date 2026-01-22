import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import CategoriesPage from './pages/CategoriesPage';
import StudiosPage from './pages/StudiosPage';
import ActressesPage from './pages/ActressesPage';
import VideoDetailPage from './pages/VideoDetailPage';

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-[#09090b] text-white">
                <Navbar />
                <main className="pt-14 px-4">
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/categories" element={<CategoriesPage />} />
                        <Route path="/studios" element={<StudiosPage />} />
                        <Route path="/actresses" element={<ActressesPage />} />
                        <Route path="/video/:code" element={<VideoDetailPage />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
