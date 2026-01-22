import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-background text-foreground">
                <Navbar />
                <main className="container mx-auto px-4 py-8">
                    <Routes>
                        <Route path="/" element={<div className="text-center mt-20">Home Page (Content Missing)</div>} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
