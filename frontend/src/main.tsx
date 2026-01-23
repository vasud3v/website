import React from 'react'
import ReactDOM from 'react-dom/client'
import './lib/jquery-setup'; // Setup jQuery globally first
import App from './App.tsx'
import './index.css';
import { ThemeProvider } from './context/ThemeContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ThemeProvider>
            <App />
        </ThemeProvider>
    </React.StrictMode>,
)
