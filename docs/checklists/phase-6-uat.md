# Phase 6 UAT Checklist - Profile and Feedback Intelligence

Date: 26-10-09
Tester: hutch
Environment/Branch: .venv main
Mongo DB Name Used: RecipeLab_phase2_uat

---

## 1) Preconditions

- [x] `.env` is valid and app is running
- [x] `GET /api/health` responds
- [x] At least one recipe and/or suggestion exists for feedback actions

---

## 2) Profile Editor UI

Manual checks at `/profile`:
- [x] Page loads and shows active profile fields
- [x] Can edit/save `likes`
- [x] Can edit/save `dislikes`
- [x] Can edit/save `hard_avoids`
- [x] Can edit/save profile notes
- [x] Saved changes persist after refresh

---

## 3) Feedback Capture Actions

Manual checks on `/recipes/<id>`:
- [x] `Liked` action saves feedback and shows success message
- [x] `Disliked` action saves feedback and shows success message
- [x] `Add Note` action saves feedback note and shows success message

Manual checks on `/suggestions/<id>`:
- [x] `Liked` action saves feedback
- [x] `Disliked` action saves feedback
- [x] `Add Note` action saves feedback note

Optional DB verification:

```bash
.venv/bin/python - <<'PY'
from app.config import AppConfig
from pymongo import MongoClient

cfg = AppConfig.from_env()
db = MongoClient(cfg.mongo_uri)[cfg.mongo_db_name]
print("feedback_events count:", db["feedback_events"].count_documents({}))
print("latest:", db["feedback_events"].find_one(sort=[("created_at", -1)]))
PY
```

- [x] Feedback events recorded in `feedback_events`

---

## 3.1) Feedback Visibility and Recall (Phase 6.1)

Manual checks on `/recipes/<id>` after saving feedback:
- [x] Current feedback section shows saved `Liked` or `Disliked` state
- [x] If a note was saved, `Note saved` indicator appears
- [x] Action button styling reflects the active selection
- [x] Recent feedback history list shows signal + note + timestamp

Manual checks on `/suggestions/<id>` after saving feedback:
- [x] Current feedback section shows saved `Liked` or `Disliked` state
- [x] If a note was saved, `Note saved` indicator appears
- [x] Action button styling reflects the active selection
- [x] Recent feedback history list shows signal + note + timestamp

Persistence recall checks:
- [x] Navigate away and return; feedback state remains visible
- [x] Feedback note input is prefilled with latest note (if present)

---

## 4) Profile Update Suggestion Generation

Manual checks at `/profile`:
- [x] Click **Generate Update Suggestions**
- [x] Pending suggestions list appears (or clear empty message if no signal)
- [x] Suggestion rows show action/token/support info

---

## 5) Apply/Reject Profile Update Suggestions

Manual checks at `/profile`:
- [x] Applying a suggestion updates active profile accordingly
- [x] Applied suggestion no longer appears in pending list
- [x] Rejecting a suggestion removes it from pending list

Optional DB verification:

```bash
.venv/bin/python - <<'PY'
from app.config import AppConfig
from pymongo import MongoClient

cfg = AppConfig.from_env()
db = MongoClient(cfg.mongo_uri)[cfg.mongo_db_name]

print("pending:", db["profile_update_suggestions"].count_documents({"status":"pending"}))
print("applied:", db["profile_update_suggestions"].count_documents({"status":"applied"}))
print("rejected:", db["profile_update_suggestions"].count_documents({"status":"rejected"}))
print("active profile:", db["preferences"].find_one({"active":True}))
PY
```

- [x] Status transitions are correct (`pending` -> `applied`/`rejected`)

Phase 6.1 visibility checks at `/profile`:
- [x] Applied suggestions appear in **Applied Suggestions** history
- [x] Rejected suggestions appear in **Rejected Suggestions** history
- [x] Pending list excludes already applied/rejected items

---

## 6) Control and Drift Safety Checks

- [x] No profile changes are auto-applied without user action
- [x] Hard avoids remain user-controlled
- [x] Suggested updates are reviewable before apply

---

## 7) Regression Test Suite

Run:

```bash
.venv/bin/python -m unittest tests.test_profile_refinement_service tests.test_web_routes tests.test_indexes -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall app tests run.py
```

- [x] Profile refinement tests pass
- [x] Web route tests pass
- [x] Full suite passes
- [x] Compile check passes

---

## 8) Validation Gate Decision

Gate requirement: user validates profile updates are useful and controllable.

Phase 6.1 additional gate requirement: user can clearly see prior feedback and profile-update outcomes.

Overall Result:
- [x] PASS - Phase 6 validation gate complete
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
