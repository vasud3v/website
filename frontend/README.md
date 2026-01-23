# Javcore Frontend

React + TypeScript + Vite frontend for the Javcore video streaming platform.

## Quick Start

From project root:
```bash
START_JAVCORE.bat
```

Or manually:
```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5174`
Backend API: `http://localhost:8000`

## Configuration

Edit `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api
```

## Development

```bash
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
```
