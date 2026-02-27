# HavenJob Backend

Django + django-ninja API for HavenJob. Part of the [havenjob](../) monorepo.

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **PostgreSQL** — the app uses Postgres as the database

## Database (PostgreSQL)

Create a database and (optional) user:

```bash
# macOS (Homebrew): brew services start postgresql@16
# Ubuntu: sudo systemctl start postgresql

psql -U postgres -c "CREATE DATABASE havenjob;"
# If you use a dedicated user:
# psql -U postgres -c "CREATE USER havenjob WITH PASSWORD 'yourpassword';"
# psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE havenjob TO havenjob;"
```

Set connection details in `.env` (see Setup below).

## Setup

From the repo root or from `backend/`:

```bash
cd backend
uv sync
```

Copy environment and set PostgreSQL variables:

```bash
cp .env.example .env
# Edit .env: set POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
```

Create and apply migrations, create a superuser:

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

## Run

```bash
uv run python manage.py runserver
```

API will be at `http://127.0.0.1:8000/` (docs: `http://127.0.0.1:8000/api/docs`).

## Docker

From the **repo root** (not `backend/`):

```bash
# Set at least POSTGRES_PASSWORD (e.g. copy backend/.env.example to .env at repo root)
cp backend/.env.example .env
# Edit .env: set POSTGRES_PASSWORD

docker compose up -d
```

**Run migrations** (one-off; use when DB is up):

```bash
docker compose run backend python manage.py migrate
```


Or inside a running backend container:  
`docker compose exec backend python manage.py migrate`

**Fresh database (fix "admin.0001_initial applied before its dependency users.0001_initial"):**  
If the DB was ever migrated with Django’s default User and you now use the custom `users.User` model, reset the DB and re-run migrations (only if you can lose existing DB data):

```bash
docker compose down -v
docker compose up -d
```

- API: http://localhost:8000  
- API docs: http://localhost:8000/api/docs  
- Migrations run automatically on startup.

**Create a superuser** (prompts for email, forwarding address, password):

```bash
docker compose exec backend uv run python manage.py createsuperuser
```

If the backend container is not running:  
`docker compose run --rm backend uv run python manage.py createsuperuser`

## Project structure

| Path | Purpose |
|------|---------|
| `config/` | Django project (settings, root URLs, WSGI/ASGI) |
| `apps/` | Django apps: `users`, `tracker`, `notifications`, `ai` |
| `providers/` | Plugin registries (email, LLM) — no models |
| `core/` | Shared utilities (auth, billing, storage, pagination) |

Each app under `apps/` follows: `models.py`, `api.py` (django-ninja router), `schemas.py`, `services.py`, `migrations/`.

## Tests

Install dev dependencies (pytest, pytest-django, coverage), then run tests:

```bash
cd backend
uv sync --extra dev
uv run pytest
```

With coverage:

```bash
uv run coverage run -m pytest
uv run coverage report
# optional: uv run coverage html && open htmlcov/index.html
```

You can also run Django’s test runner: `uv run python manage.py test`. Tests use an in-memory SQLite DB by default (no PostgreSQL required).

## Common commands (with uv)

| Command | Description |
|---------|-------------|
| `uv sync --extra dev` | Install deps including dev (pytest, coverage) |
| `uv run pytest` | Run tests |
| `uv run python manage.py startapp users apps/users` | Create a new app under `apps/` |
| `uv run python manage.py runserver` | Start dev server |
| `uv run python manage.py migrate` | Apply migrations |
| `uv run python manage.py makemigrations` | Create migrations after model changes |
| `uv run python manage.py createsuperuser` | Create admin user |
| `uv run python manage.py shell` | Django shell |

## Docs

- [Implementation plan](../docs/implementation-plan.md)
- [Database schema](../docs/database-schema.md)
- [PRD](../docs/PRD.md)
