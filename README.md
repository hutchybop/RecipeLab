# RecipeLab

RecipeLab is a Flask + MongoDB app for managing a personal recipe library, importing markdown recipes, and generating recipe suggestions with an LLM.

## Features

- Recipe dashboard and browser (`/`, `/recipes`)
- Recipe CRUD flows (view, edit, soft-delete)
- AI suggestion generation (`/generate`, `POST /api/generate`)
- Raw recipe conversion/import flow (`/import`)
- Suggestion review workflow (draft / draft_invalid / accepted / rejected)
- Profile preferences and profile update suggestions (`/profile`)
- Runtime model selection (`/settings`)
- PDF export for recipes (`/recipes/<id>/pdf`)
- Health endpoint (`GET /api/health`)

## Tech Stack

- Python 3.12+
- Flask
- PyMongo (MongoDB)
- OpenAI SDK (OpenAI-compatible endpoint support)
- Gunicorn
- Black + Flake8

## Project Structure

```text
app/
  blueprints/      # Web + API routes
  repositories/    # MongoDB data access + indexes
  services/        # Generation, prompts, schema normalization, PDF export
  templates/       # Jinja templates
  config.py        # Env config + validation
  extensions.py    # Mongo client/db wiring
docs/              # Project docs
recipes/           # Markdown recipe library
scripts/           # Import utilities
tests/             # unittest suite
run.py             # App entrypoint (run:app)
```

## Prerequisites

- Python 3.12+
- MongoDB instance (Atlas or local)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Create local env file:

```bash
cp .env.example .env
```

Required at startup:

- `SECRET_KEY`
- `MONGO_URI`

Notes:

- `MONGO_DB_NAME` defaults to `recipelab` if not set.
- LLM features require provider/model vars (`LLM_PROVIDER`, `LLM_MODEL`, optional `LLM_ALLOWED_MODELS`, etc.).

## Run Locally

```bash
python run.py
```

App binds to `0.0.0.0:3009`.

## Run with Docker

```bash
docker compose up --build
```

Serves on `http://localhost:3009` (`3009:3009` in compose, env loaded from `.env`).

## Smoke Check

- Open `http://localhost:3009/`
- Check health:

```bash
curl -i http://localhost:3009/api/health
```

## API

### `GET /api/health`

Returns service health. If Mongo ping fails, returns `503` with `status: degraded`.

### `POST /api/generate`

Request:

```json
{
  "meal_type": "main",
  "instructions": "high-protein dinner",
  "model": "optional-model-override"
}
```

Valid `meal_type` values:

- `main`
- `lunch_batch`
- `lunch_single`
- `breakfast`
- `dessert`

Response:

- `201` for valid draft suggestion
- `422` for `draft_invalid`
- `400` for invalid meal type
- `503` if backend/database is unavailable

## Import Existing Markdown Recipes

Use the import script:

```bash
python scripts/import_markdown_recipes.py
```

Useful flags:

- `--recipes-dir recipes`
- `--exclude-dir "AI-suggested"` (repeatable)
- `--dry-run`

## Tests

Run all tests:

```bash
python -m unittest discover -s tests
```

## Lint / Format

```bash
flake8 .
black .
```

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE).
