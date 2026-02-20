# In a Year

`In a Year` shows yearly stats from connected services like Trakt and Hardcover.

## Stack

- Backend: FastAPI + SQLAlchemy
- Frontend: Nuxt 3 + Tailwind
- Data/Jobs: PostgreSQL + Redis + Celery

## Quick Start

1. Copy env file:
   `cp .env.example .env`
2. Start infra:
   `docker compose -f docker-compose-dev.yml up -d db redis`
3. Run backend:
   `uv run uvicorn backend.main:app --reload --port 8000`
4. Run frontend:
   `cd frontend && npm install && npm run dev`

## API

- Base URL: `http://localhost:8000/api/v1`
- Docs: `http://localhost:8000/docs`
