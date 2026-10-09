# Phase 4 UAT Checklist - Core UI (Friendly MVP)

Date: 26-10-08
Tester: Hutch
Environment/Branch: .venv main
Mongo DB Name Used: recipelab_phase2_uat

---

## 1) Preconditions

- [x] `.env` is present and valid (`SECRET_KEY`, `MONGO_URI`, LLM vars)
- [x] App is running (`python run.py` or Docker)
- [x] `GET /api/health` responds
- [x] Test data exists (recipes and/or suggestions)

---

## 2) Dashboard and Navigation

Run:

```bash
curl -sS http://localhost:3009/ > /dev/null
```

Manual checks in browser:
- [x] Dashboard loads at `/`
- [x] Cards show counts for saved recipes, draft suggestions, invalid suggestions
- [x] Top navigation links work: Generate, Suggestions, Recipe Library

---

## 3) Generate Page Flow

Manual checks at `/generate`:
- [x] Page loads with meal type selector, model override, instructions input
- [x] Submitting a valid generation request redirects to suggestion detail page
- [x] Success flash message appears for valid `draft` suggestion
- [ ] Warning flash appears for `draft_invalid`
- [x] Invalid meal type is handled with clear error message

---

## 4) Suggestions Review Flow

Manual checks at `/suggestions` and `/suggestions/<id>`:
- [x] Suggestions list loads and status filter works (`draft`, `draft_invalid`, `accepted`, `rejected`, `all`)
- [x] Suggestion detail shows metadata, ingredients, method, and validation errors (if any)
- [x] Status badges are visually clear
- [x] `Reject` action updates status and returns to suggestions list

---

## 5) Save to Recipe Library Flow

Manual checks from a `draft` suggestion detail page:
- [x] `Save to Recipe Library` action is available for `draft`
- [x] Save action redirects to recipe detail page
- [x] Suggestion status updates to `accepted`
- [x] New recipe appears in `/recipes`

---

## 6) Recipe Library and Detail

Manual checks at `/recipes` and `/recipes/<id>`:
- [x] Recipe list loads
- [x] Meal type filter updates list correctly
- [x] Source badge (`ai`/`user`) is shown in list/detail
- [x] Recipe detail renders metadata, ingredients, method, and notes (if present)

---

## 7) Error and Empty States

Manual checks:
- [x] Visiting a non-existent suggestion ID shows friendly message and redirects safely
- [x] Visiting a non-existent recipe ID shows friendly message and redirects safely
- [x] Empty list states are clear for suggestions and recipes

---

## 8) Regression Test Suite

Run:

```bash
.venv/bin/python -m unittest tests.test_web_routes -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall app tests run.py
```

Checks:
- [x] Web route tests pass
- [x] Full test suite passes
- [x] Compile check passes

---

## 9) Validation Gate Decision

Gate requirement: user can complete **generate -> review -> save** without API tooling.

Overall Result:
- [x] PASS - Phase 4 validation gate complete
- [ ] FAIL - remediation required

Notes / Issues Found:

```
3. Generate Page Flow: Unable to test 'Warning flash appears for `draft_invalid`
AI always produces correct format
```

Remediation Tasks (if any):

```
N/A
```

Sign-off:
- Name: hutch
- Date: 26-10-09
