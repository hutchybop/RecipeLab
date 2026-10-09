# Phase 3 UAT Checklist - AI Generation Pipeline

Date: 26-10-09
Tester: hutch
Environment/Branch: .venv main
Mongo DB Name Used: recipelab_phase2_uat
LLM Provider/Model Used: opencode zen & gpt-5.4

---

## 1) Preconditions

- [x] `.env` is present and contains `SECRET_KEY` and `MONGO_URI`
- [x] `.env` contains `LLM_PROVIDER`, `LLM_MODEL`, and (if required) `LLM_API_KEY`
- [x] App is running locally (`python run.py`) or in Docker
- [x] `GET /api/health` returns API reachable status

Recommended `.env` values for OpenCode Zen:

```env
LLM_PROVIDER=openai_compatible
LLM_ENDPOINT=https://opencode.ai/zen/v1
LLM_MODEL=gpt-5.4
LLM_API_KEY=...
```

Notes:
- SDK-based routing now chooses endpoint style by model.
- `gpt-*` models use Responses API.
- Non-GPT Zen models (example: `deepseek-v4-flash`) use Chat Completions API.
- Backward-compatible endpoint values with `/responses` or `/chat/completions` still work.

---

## 2) Baseline Endpoint Validation

Run:

```bash
curl -sS http://localhost:3009/api/health | python -m json.tool
```

Checks:
- [x] Endpoint reachable
- [x] JSON response shape is valid

---

## 3) Controlled Generation Requests

### 3.1 Successful generation request (GPT model)

Run:

```bash
curl -sS -X POST http://localhost:3009/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "main",
    "instructions": "High-protein, one-pan, under 40 minutes, no peanuts or cauliflower"
  }' | python -m json.tool
```

Checks:
- [x] HTTP status `201`
- [x] `status` is `draft`
- [x] `run_id` and `suggestion_id` are present
- [x] `validation.valid` is `true`
- [x] `recipe` contains title, ingredients, method

### 3.2 Model-routed endpoint check (non-GPT model)

Run (optional if model access is available):

```bash
curl -sS -X POST http://localhost:3009/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "meal_type": "main",
    "model": "deepseek-v4.1-flash",
    "instructions": "Quick spicy chicken dinner"
  }' | python -m json.tool
```

Checks:
- [x] Request succeeds (201 or 422 depending on model output quality)
- [x] `run_id` present
- [x] Stored run model matches override (`deepseek-v4.1-flash`)

### 3.3 Invalid meal type request

Run:

```bash
curl -sS -o /tmp/phase3_invalid_meal.json -w "%{http_code}\n" \
  -X POST http://localhost:3009/api/generate \
  -H "Content-Type: application/json" \
  -d '{"meal_type":"snack","instructions":"quick"}'

cat /tmp/phase3_invalid_meal.json | python -m json.tool
```

Checks:
- [x] HTTP status `400`
- [x] Error explains invalid `meal_type`

---

## 4) Persistence and Traceability Verification

Run:

```bash
.venv/bin/python - <<'PY'
from app.config import AppConfig
from pymongo import MongoClient

cfg = AppConfig.from_env()
db = MongoClient(cfg.mongo_uri)[cfg.mongo_db_name]

print("suggestions count:", db["suggestions"].count_documents({}))
print("generation_runs count:", db["generation_runs"].count_documents({}))

latest_suggestion = db["suggestions"].find_one(sort=[("created_at", -1)])
latest_run = db["generation_runs"].find_one(sort=[("created_at", -1)])

print("\nLatest suggestion:")
print({
    "_id": str(latest_suggestion.get("_id")) if latest_suggestion else None,
    "status": latest_suggestion.get("status") if latest_suggestion else None,
    "meal_type": latest_suggestion.get("meal_type") if latest_suggestion else None,
    "generation_run_id": latest_suggestion.get("generation_run_id") if latest_suggestion else None,
    "validation": latest_suggestion.get("validation") if latest_suggestion else None,
})

print("\nLatest run:")
print({
    "_id": str(latest_run.get("_id")) if latest_run else None,
    "status": latest_run.get("status") if latest_run else None,
    "meal_type": latest_run.get("meal_type") if latest_run else None,
    "model": latest_run.get("model") if latest_run else None,
    "provider": latest_run.get("provider") if latest_run else None,
})
PY
```

Checks:
- [x] At least one new `suggestions` document created
- [x] At least one new `generation_runs` document created
- [x] Suggestion references generation run via `generation_run_id`
- [x] Run has terminal status (`succeeded` or `failed`)

---

## 5) Constraint Adherence Spot-Check

From generated `recipe.ingredients`, check hard avoids are absent:

- [x] Whole chickpeas not present
- [x] Peanuts not present
- [x] Sprouts not present
- [x] Cauliflower not present
- [x] Cinnamon not present

---

## 6) Regression + New Routing Tests

Run:

```bash
.venv/bin/python -m unittest tests.test_llm_adapter -v
.venv/bin/python -m unittest tests.test_generate_api -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall app scripts tests run.py
```

Checks:
- [x] Adapter routing tests pass (`tests.test_llm_adapter`)
- [x] Generate API tests pass (`tests.test_generate_api`)
- [x] Full test suite passes
- [x] Compile check passes

---

## 7) Result and Sign-Off

Overall Result:
- [x] PASS - Phase 3 validation gate complete
- [ ] FAIL - remediation required

Notes / Issues Found:

```
Step 3.2 amended: Some Zen non-GPT models unavailable for this account/workspace.
Observed provider responses:
- deepseek-v4-flash: 400 Endpoint is unavailable
- deepseek-v4.1-flash: 201 Endpoint reached
```

Remediation Tasks (if any):

```
Nil
```

Sign-off:
- Name: hutch
- Date: 26-10-09
