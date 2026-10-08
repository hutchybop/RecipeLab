# Recipe App Project Plan

## Purpose

This document is the working implementation plan for the personal recipe app.
It is designed to be readable by humans and AI agents.

Primary use:
- Keep development aligned to agreed scope.
- Define phase gates before moving forward.
- Record updates at each checkpoint.

---

## Product Vision

Build a local-only, single-user web app that helps generate, manage, and refine recipes using AI while preserving user control over final content.

Core loop:
1. Generate recipe with constraints.
2. Review/edit recipe.
3. Save or discard.
4. Capture feedback.
5. Improve profile and future suggestions.

---

## Scope Lock (Current)

### Functional Requirements
- Friendly, easy-to-use UI.
- Generate one recipe at a time (no batch generation in MVP).
- Meal types: `main`, `lunch_batch`, `lunch_single`, `breakfast`, `dessert`.
- Free-text instruction input (chat-style prompt guidance).
- Recipe library view with meal-type categorization.
- AI/user origin shown as badges; no separate AI category.
- Recipe CRUD: create, read, update, delete.
- Raw recipe input -> AI converts to canonical format -> user review/edit -> save.
- Tasting profile editable in UI.
- Backend profile refinement via controlled suggestions (user-approved updates).
- PDF export for recipes.
- In-app model selection only (from allowed list).

### Configuration Rules
- AI provider, endpoint, and API key are configured via `.env` only.
- Changing provider/endpoint/key requires restart (Docker container restart expected).
- No in-app editing of API key/provider/endpoint.

### Non-Functional Requirements
- Stack: Python, Flask, MongoDB Atlas, Bootstrap (latest stable).
- Single user; no user accounts.
- Local-only personal use; no public deployment target.
- Dockerized runtime.
- Source in GitHub repository.
- CI builds and publishes Docker image to GHCR (`ghcr.io`).

---

## Architecture Overview

### High-Level Components
- Flask app (web pages + JSON API endpoints).
- MongoDB Atlas as primary data store.
- LLM provider adapter service.
- Prompt composition service.
- Validation service (schema + hard constraints).
- Profile refinement service.
- Markdown import/export service.
- PDF export service.

### Suggested Project Structure
- `app/__init__.py` app factory.
- `app/config.py` environment configuration.
- `app/extensions.py` DB and shared extensions.
- `app/blueprints/web/routes.py` server-rendered UI routes.
- `app/blueprints/api/routes.py` JSON API routes.
- `app/services/` business logic.
- `app/repositories/` Mongo data access.
- `templates/` Jinja templates.
- `static/` CSS/JS assets.
- `scripts/` utility scripts (import/export/rebuild profile).
- `prompts/templates/` prompt templates by meal type.

---

## Data Model (MVP)

### Collections
- `recipes`
  - Canonical saved recipes (accepted AI or user-created).
  - Includes meal type, metadata, structured ingredients/method, source type, timestamps.

- `suggestions`
  - AI-generated candidates before acceptance.
  - Includes status (`draft`, `accepted`, `rejected`, `draft_invalid`), validation results, run reference.

- `preferences`
  - Active tasting profile and structured preference weights/rules.

- `feedback_events`
  - User signals (`liked`, `disliked`, notes) on recipes/suggestions.

- `generation_runs`
  - Prompt/model audit data for traceability and debugging.

### Constraints
- Preserve hard dislikes as strict validation filters unless explicitly edited by user.
- Keep canonical recipe schema consistent across import, generation, and edits.

---

## Phase Plan

Each phase includes: objective, deliverables, testing, and validation gate.
Do not advance phase status to complete until gate criteria are met.

### Phase 0 - Product Contract and UX Wireframe

Objective:
- Finalize flows and acceptance criteria.

Deliverables:
- Confirmed feature contract.
- Page/flow map for: generate, review, library, edit/delete, profile, settings, export.
- MVP/non-goal list documented.

Testing:
- Requirements consistency review.

Validation Gate:
- User signs off on flow and field list.

Exit Criteria:
- No unresolved requirement ambiguities.

---

### Phase 1 - Project Foundation

Objective:
- Establish runnable app baseline.

Deliverables:
- Flask scaffold with app factory and blueprints.
- MongoDB connection and health endpoint.
- Dockerfile + docker-compose.
- `.env.example` and startup config validation.

Testing:
- App boot smoke test.
- Config validation tests.
- DB connection smoke test.

Validation Gate:
- User can run app locally via Docker with healthy startup.

Exit Criteria:
- Stable baseline for feature development.

---

### Phase 2 - Data Model and Repositories

Objective:
- Implement reliable persistence layer.

Deliverables:
- Repository modules for all collections.
- Collection indexes.
- Schema validation/normalization utilities.
- Optional markdown import script for existing recipes.

Testing:
- Repository unit tests.
- Schema validation tests.
- Index presence checks.

Validation Gate:
- User verifies imported/seeded data shape and usability.

Exit Criteria:
- Persistent storage supports all planned workflows.

---

### Phase 3 - AI Generation Pipeline

Objective:
- Generate one constrained recipe per request.

Deliverables:
- Prompt composer (meal type + profile + manual instructions + constraints).
- LLM adapter using `.env` provider settings.
- `POST /api/generate` flow.
- Structured parsing + validation + suggestion persistence.
- Generation run logging.

Testing:
- Prompt assembly unit tests.
- Mocked provider integration tests.
- Invalid output handling tests.

Validation Gate:
- User runs controlled generation set and confirms output quality baseline.

Exit Criteria:
- Reliable single-recipe generation with traceability.

---

### Phase 4 - Core UI (Friendly MVP)

Objective:
- Deliver user-friendly end-to-end screens.

Deliverables:
- Bootstrap-based pages: dashboard, generate, suggestions, recipe library, recipe detail.
- Meal-type filters and AI/user badges.
- Clear error/success states.

Testing:
- Route/template tests.
- Basic responsive checks.
- Manual usability walkthrough.

Validation Gate:
- User completes generate -> review -> save flow without API tooling.

Exit Criteria:
- Stable and understandable MVP UI.

---

### Phase 5 - Recipe Lifecycle Features

Objective:
- Complete core recipe management and import conversion.

Deliverables:
- Edit recipe flow.
- Delete recipe flow (soft-delete recommended first).
- Raw recipe input + AI canonical conversion.
- Review/edit-before-save confirmation step.
- Accept/reject suggestion actions.

Testing:
- CRUD integration tests.
- Delete behavior tests.
- Conversion flow tests.

Validation Gate:
- User successfully edits, deletes, imports, and saves multiple recipes.

Exit Criteria:
- Full recipe lifecycle operational.

---

### Phase 6 - Profile and Feedback Intelligence

Objective:
- Improve future output quality via feedback loop.

Deliverables:
- Tasting profile editor UI.
- Feedback actions on recipes/suggestions.
- Profile update suggestion engine.
- User approval/rejection workflow for profile changes.

Testing:
- Profile suggestion logic tests.
- Workflow integration tests.

Validation Gate:
- User validates that suggested profile updates are useful and controllable.

Exit Criteria:
- Feedback loop improves recommendations without unwanted profile drift.

---

### Phase 7 - PDF Export and Runtime Settings UX

Objective:
- Add export and model-level runtime controls.

Deliverables:
- Simple recipe PDF export.
- Settings page for model selection only.
- Read-only display for provider/endpoint source (`.env` managed).

Testing:
- PDF content/render tests.
- Settings persistence tests.

Validation Gate:
- User confirms PDF quality and model-switch behavior.

Exit Criteria:
- Utility features complete for personal daily use.

---

### Phase 8 - Docker Release and GHCR Automation

Objective:
- Ship reliable container builds through GitHub.

Deliverables:
- GitHub Actions workflow: test -> build -> push image to GHCR.
- Tagging strategy (`latest`, semver/tag, short SHA).
- Deployment/runbook documentation.

Testing:
- CI pipeline pass on PR/main.
- Pull/run GHCR image on clean environment.

Validation Gate:
- User deploys from GHCR image and passes smoke checklist.

Exit Criteria:
- Repeatable image delivery and personal deployment flow.

---

## Testing Strategy (Cross-Phase)

### Test Layers
- Unit tests: validators, prompt builder, repositories, profile logic.
- Integration tests: Flask endpoints + test DB.
- End-to-end smoke tests: core user journeys.
- Regression scenarios: fixed prompt cases for quality checks.

### Quality Gates
- No phase completion without passing required tests.
- Any failed validation gate blocks advancement.

---

## User Validation Framework

At each phase checkpoint:
1. Run phase-specific manual checklist.
2. Score 1-5 on usability, quality, speed, trust.
3. If any score is below 4, create remediation tasks before next phase.

Suggested artifacts:
- `docs/checklists/phase-X-uat.md`
- `docs/decisions/` ADR-style notes for major tradeoffs.

---

## Risks and Mitigations

- Prompt inconsistency or malformed model output
  - Mitigation: strict parser + validator + `draft_invalid` status.

- Preference drift from noisy edits
  - Mitigation: profile updates are suggested, not auto-applied.

- Duplicate/near-duplicate recipes
  - Mitigation: title + ingredient similarity checks with warning.

- Config confusion around model/provider
  - Mitigation: clear settings UI with read-only provider/endpoint note.

- Local-only but accidental exposure
  - Mitigation: bind to local interface by default; document safe Docker networking.

---

## Definition of Done (MVP)

MVP is complete when all are true:
- Single recipe generation by meal type with manual user instructions.
- Review/edit/save/delete recipe workflows function reliably.
- Recipe library supports category filtering and AI/user origin badges.
- Raw recipe import conversion supports review before final save.
- Tasting profile can be edited and refined through approval workflow.
- Recipe PDF export works.
- App runs in Docker locally.
- GHCR image can be built, pushed, pulled, and run.

---

## Plan Maintenance Protocol

Update this file at every checkpoint.

### Update Rules
- Do not remove prior decisions; append updates with date.
- Mark phase status explicitly: `not_started`, `in_progress`, `blocked`, `complete`.
- Record key deviations and rationale.
- Keep scope changes in a dedicated log section.

### Phase Status Tracker
- Phase 0: `complete`
- Phase 1: `complete`
- Phase 2: `complete`
- Phase 3: `not_started`
- Phase 4: `not_started`
- Phase 5: `not_started`
- Phase 6: `not_started`
- Phase 7: `not_started`
- Phase 8: `not_started`

### Checkpoint Log Template

Use this template for each checkpoint entry:

```md
## Checkpoint YYYY-MM-DD

- Phase: <number/name>
- Status: <in_progress|blocked|complete>
- What changed:
  - ...
- Tests run:
  - ...
- User validation outcome:
  - ...
- Risks/issues:
  - ...
- Decision(s):
  - ...
- Next actions:
  - ...
```

---

## Checkpoint 2026-10-07

- Phase: 1 / Project Foundation
- Status: `complete`
- What changed:
  - Added Flask app scaffold with app factory, config loader, and blueprint registration.
  - Added Mongo extension wiring and health endpoint (`/api/health`) with service status payload.
  - Added Docker baseline (`Dockerfile`, `docker-compose.yml`) and environment template (`.env.example`).
  - Added runtime entrypoint (`run.py`) and dependency manifest (`requirements.txt`).
- Tests run:
  - `python3 -m compileall app run.py`
  - `SECRET_KEY=test-key MONGO_URI=mongodb://localhost:27017 MONGO_DB_NAME=recipes_test .venv/bin/python` app test-client smoke checks for `/` and `/api/health`.
- User validation outcome:
  - Pending user walkthrough in local Docker environment.
- Risks/issues:
  - Health endpoint returns degraded status when MongoDB is unavailable, which is expected for disconnected local test runs.
- Decision(s):
  - Keep startup config strict for required env vars (`SECRET_KEY`, `MONGO_URI`).
  - Keep provider/endpoint/API key management out of UI and env-driven only.
- Next actions:
  - Begin Phase 2 (data model and repository layer).

---

## Checkpoint 2026-10-08

- Phase: 2 / Data Model and Repositories
- Status: `in_progress`
- What changed:
  - Added schema normalization and validation utilities for recipes, suggestions, preferences, feedback events, and generation runs.
  - Added repository modules for all Phase 2 collections under `app/repositories/`.
  - Added collection index definitions and an aggregate `ensure_all_indexes()` helper.
  - Added optional markdown import script `scripts/import_markdown_recipes.py` for seeding/upserting `recipes/` content.
  - Added Phase 2 test suite under `tests/` (schema, repository, and index checks).
- Tests run:
  - `.venv/bin/python -m unittest discover -s tests -v`
  - `.venv/bin/python -m compileall app scripts tests run.py`
- User validation outcome:
  - Pending user verification of imported/seeded data shape and usability.
- Risks/issues:
  - Import script maps meal type by recipe path conventions; new folder structures may need mapping updates.
- Decision(s):
  - Keep repository and schema layers framework-agnostic so they can be reused by future API/UI phases.
  - Keep index creation explicit via helper call instead of app-start auto-run to preserve degraded startup behavior when Mongo is unavailable.
- Next actions:
  - Run the import script against the target MongoDB and confirm data shape for Phase 2 gate.
  - Integrate repositories into generation endpoints during Phase 3.

---

## Checkpoint 2026-10-08 (Phase 2 Validation Gate - Pending Finalization)

- Phase: 2 / Data Model and Repositories
- Status: `in_progress`
- What changed:
  - Executed Phase 2 UAT checklist (`docs/checklists/phase-2-uat.md`).
  - Ran real markdown import and validated stored recipe shape/usability.
  - Verified required collection indexes are present.
- Tests run:
  - `.venv/bin/python scripts/import_markdown_recipes.py`
  - Data-shape verification commands from `docs/checklists/phase-2-uat.md`
  - Index verification commands from `docs/checklists/phase-2-uat.md`
- User validation outcome:
  - `pass`
- Risks/issues:
  - `none`
- Decision(s):
  - `N/A`
- Next actions:
  - If PASS: set Phase 2 status tracker to `complete` and begin Phase 3.
  - If FAIL: add remediation tasks and keep Phase 2 `in_progress`.

---

## Change Log

### 2026-10-07
- Initial project plan created from agreed requirements and phased delivery strategy.
- Phase 1 scaffold completed with health check and Docker baseline.

### 2026-10-08
- Phase 2 persistence foundation added (schemas, repositories, indexes, tests, and markdown import tooling).
