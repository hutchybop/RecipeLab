# AGENTS.md

## Current Repo Reality
- This repo is both a Flask app and a recipe markdown library; do not assume markdown-only.
- GitHub Actions Docker release workflow exists at `.github/workflows/docker-release.yml`.
- Lint/format config is defined in `.flake8` (flake8) and `pyproject.toml` (black).
- Responsive UI validation checklists are in `docs/checklists/phase-9-uat.md`, `phase-10-uat.md`, and `phase-11-uat.md`.

## Setup and Run
- Create env and install deps: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install -r requirements-dev.txt`
- Local run (non-Docker): `python run.py` (binds `0.0.0.0:3009`)
- Docker run: `docker compose up --build` (maps `3009:3009`, loads env from `.env`)
- Smoke check: open `/` (dashboard page), then call `GET /api/health` on the active port

## Required Environment
- App startup fails if `SECRET_KEY` or `MONGO_URI` is missing (`AppConfig.validate()` in `app/config.py`).
- Copy `.env.example` to `.env`; `load_dotenv()` is called in `app/config.py`, so local runs load it automatically.
- `MONGO_DB_NAME` defaults to `recipelab` in code if unset.
- LLM features (`/generate`, `/import`, `POST /api/generate`) additionally rely on `LLM_PROVIDER` + model settings (`LLM_MODEL`, optional `LLM_ALLOWED_MODELS`, etc.); if missing/misconfigured, generation returns errors but app startup still succeeds.

## Code Map (High Signal)
- `run.py` creates `app` via `create_app()` and is also the gunicorn target (`run:app`).
- `app/__init__.py` wires config validation, extension init, and blueprint registration.
- `app/extensions.py` creates/stores `MongoClient` and DB handle in `app.extensions`.
- `app/blueprints/web/routes.py` serves the web UI (`/` dashboard, `/recipes`, `/suggestions`, `/generate`, `/import`, `/profile`, `/settings`, edit/delete flows, PDF export).
- `/` renders `app/templates/dashboard.html`.
- `app/templates/base.html` contains global responsive navigation + accessibility anchors (skip link, active nav states).
- `app/blueprints/api/routes.py` exposes `GET /api/health` and `POST /api/generate`.
- `app/services/generation_service.py` handles LLM generation/conversion and writes generation runs + suggestions.
- `app/repositories/*` contains MongoDB repositories and index management (`ensure_all_indexes`).

## Recipe Content Conventions
- Recipe source files are under `recipes/` (`main/`, `lunch/`, `dessert/`, `AI-suggested/`).
- Import script: `scripts/import_markdown_recipes.py` parses markdown recipes and maps paths to meal types (`main`, `lunch_batch`, `lunch_single`, `dessert`).
- For recipe normalization, follow `prompts/canonical_recipe_formatter_prompt.md`.
- Keep canonical sections/frontmatter (`title`, `source`, `servings`, `prep_time`, `cook_time`, `rating`, `difficulty`, `tags`, then `## Ingredients`, `## Method`, optional `## Notes`).
- Do not invent missing metadata; leave fields empty.
- Normalize ingredients as quantity + unit + ingredient; use `Method` (not `Preparation Steps`).
- Respect hard avoids from `tasting-profile.md`: whole chickpeas, peanuts, sprouts, cauliflower, cinnamon.
