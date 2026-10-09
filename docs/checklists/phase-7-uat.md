# Phase 7 UAT Checklist - PDF Export and Runtime Settings UX

Date: 26-10-09
Tester: hutch
Environment/Branch: .venv main
Mongo DB Name Used: recipelab_phase2_uat

---

## 1) Preconditions

- [x] `.env` is valid and app is running
- [x] `GET /api/health` responds
- [x] At least one non-deleted recipe exists
- [x] `LLM_PROVIDER`, `LLM_ENDPOINT`, `LLM_MODEL` are set
- [x] Optional: `LLM_ALLOWED_MODELS` is set to a comma-separated allow list

---

## 2) Settings Page and Model Selection

Manual checks at `/settings`:
- [x] Page loads and shows Runtime Settings
- [x] Provider is displayed read-only
- [x] Endpoint is displayed read-only
- [x] Model selector only shows allowed values
- [x] Saving model shows success flash
- [x] Saved model remains selected after refresh

Optional DB verification:

```bash
.venv/bin/python - <<'PY'
from app.config import AppConfig
from pymongo import MongoClient

cfg = AppConfig.from_env()
db = MongoClient(cfg.mongo_uri)[cfg.mongo_db_name]
print(db["runtime_settings"].find_one({"key": "generation_model"}))
PY
```

- [x] `runtime_settings` stores selected model

---

## 3) Generation/Import Use Selected Model

Manual checks:
- [x] `/generate` shows current model (read-only)
- [x] `/import` shows current model (read-only)
- [x] After changing model in settings, both pages reflect the new active model

Optional verification:
- [x] New generation run entries show updated model in `generation_runs.model`

---

## 4) PDF Export

Manual checks on `/recipes/<id>`:
- [x] **Export PDF** action is visible
- [x] Click downloads a `.pdf` file
- [x] PDF opens in viewer without corruption
- [x] PDF includes recipe title, metadata, ingredients, and method text

---

## 5) Regression Test Suite

Run:

```bash
.venv/bin/python -m unittest tests.test_web_routes tests.test_runtime_settings tests.test_repositories tests.test_indexes -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall app tests run.py
```

- [x] Web route tests pass
- [x] Runtime settings tests pass
- [x] Full suite passes
- [x] Compile check passes

---

## 6) Validation Gate Decision

Gate requirement: user confirms PDF quality and model-switch behavior.

Overall Result:
- [x] PASS - Phase 7 validation gate complete
- [ ] FAIL - remediation required

Notes / Issues Found:

```
Nil
```

Remediation Tasks (if any):

```
Nil
```

Sign-off:
- Name: hutch
- Date: 26-10-09
