# Javcore Backend API

Professional FastAPI backend server for the Javcore video streaming platform.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py       # API router aggregator
│   │       └── endpoints/   # API endpoints
│   │           ├── __init__.py
│   │           ├── videos.py
│   │           ├── categories.py
│   │           ├── studios.py
│   │           ├── cast.py
│   │           └── search.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── video.py         # Pydantic models
│   └── services/
│       ├── __init__.py
│       └── video_service.py # Business logic
├── requirements.txt
├── .env.example
├── run.bat
└── README.md
```

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Running

```bash
run.bat
```

Or: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

