# sentinelcase

Phase 1 baseline for a self-hosted security case management platform.

## Quick start

1. `cp .env.example .env`
2. `docker compose up -d --build`
3. `docker compose exec api alembic upgrade head`
4. `docker compose exec api python -m sentinelcase.bootstrap`

API docs: `http://localhost:8000/docs`
