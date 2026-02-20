# AGENTS

## Project Summary

`In a Year` collects and serves yearly activity stats from external services.

## Repo Map

- `backend/`: FastAPI app, API routes, services, DB models, Celery tasks
- `frontend/`: Nuxt app
- `ml/`: recommendation model code
- `docs/`: project docs

## Local Run

1. `cp .env.example .env`
2. `docker compose -f docker-compose-dev.yml up -d db redis`
3. Backend: `uv run uvicorn backend.main:app --reload --port 8000`
4. Frontend: `cd frontend && npm install && npm run dev`

## Notes for Agents

- Keep changes small and focused.
- Prefer `rg` for search.
- If editing API behavior, update related schema/route/service together.
