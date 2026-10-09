# AGENTS.md

## Current Repo Reality
- This repo is both a Flask app and a recipe markdown library; do not assume markdown-only.
- GitHub Actions Docker release workflow exists at `.github/workflows/docker-release.yml`.
- Lint/format config is defined in `.flake8` and `pyproject.toml`.

## Setup and Run
- Create env and install deps: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install -r requirements-dev.txt`
- Local run (non-Docker): `python run.py` (binds `0.0.0.0:3009`)
- Docker run: `docker compose up --build` (serves on `http://localhost:5000`)
- Smoke check: open `/` and call `GET /api/health` on the active port

## Required Environment
- App startup fails if `SECRET_KEY` or `MONGO_URI` is missing (`AppConfig.validate()` in `app/config.py`).
- Copy `.env.example` to `.env`; `load_dotenv()` is called in `app/config.py`, so local runs load it automatically.
- `MONGO_DB_NAME` defaults to `recipelab` in code if unset.

## Code Map (High Signal)
- `run.py` creates `app` via `create_app()` and is also the gunicorn target (`run:app`).
- `app/__init__.py` wires config validation, extension init, and blueprint registration.
- `app/extensions.py` creates/stores `MongoClient` and DB handle in `app.extensions`.
- `app/blueprints/web/routes.py` serves `/` using `app/templates/index.html`.
- `app/blueprints/api/routes.py` serves `/api/health`; returns `503` + `{"status":"degraded"}` if Mongo ping fails.
- Root `templates/` is currently unused.

## Recipe Content Conventions
- Recipe source files are under `recipes/` (`main/`, `lunch/`, `dessert/`, `AI-suggested/`).
- For recipe normalization, follow `prompts/canonical_recipe_formatter_prompt.md`.
- Keep canonical sections/frontmatter (`title`, `source`, `servings`, `prep_time`, `cook_time`, `rating`, `difficulty`, `tags`, then `## Ingredients`, `## Method`, optional `## Notes`).
- Do not invent missing metadata; leave fields empty.
- Normalize ingredients as quantity + unit + ingredient; use `Method` (not `Preparation Steps`).
- Respect hard avoids from `tasting-profile.md`: whole chickpeas, peanuts, sprouts, cauliflower, cinnamon.
