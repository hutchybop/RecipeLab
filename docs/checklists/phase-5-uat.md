# Phase 5 UAT Checklist - Recipe Lifecycle Features

Date: 26-10-09
Tester: hutch
Environment/Branch: .venv main
Mongo DB Name Used: recipelab_phase2_uat

---

## 1) Preconditions

- [x] `.env` is present and valid (`SECRET_KEY`, `MONGO_URI`, LLM vars)
- [x] App is running (`python run.py` or Docker)
- [x] `GET /api/health` responds
- [x] At least one suggestion exists (or can be generated/imported)

---

## 2) Edit Recipe Flow

Manual checks:
- [x] Open `/recipes` and enter a recipe detail page
- [x] Click **Edit Recipe**
- [x] Update title and at least one metadata field (eg. tags/rating)
- [x] Save changes
- [x] Redirects back to recipe detail
- [x] Updated values are visible in recipe detail/list

---

## 3) Delete Recipe Flow (Soft Delete)

Manual checks:
- [x] Open recipe detail page
- [x] Click **Delete Recipe** and confirm
- [x] Redirects to `/recipes`
- [x] Deleted recipe no longer appears in recipe list
- [x] Direct URL `/recipes/<id>` shows not found/redirect behavior

---

## 4) Raw Recipe Import + Conversion

Manual checks at `/import`:
- [x] Page loads with meal type, optional model override, and raw text box
- [x] Submitting empty raw text shows clear warning
- [x] Submitting valid raw text triggers conversion and redirects to suggestion detail
- [x] Success case shows `draft` suggestion ready for review
- [x] Validation failure case shows `draft_invalid` warning with review option

Suggested raw text sample:

```text
Chicken Pilaf

Serves 2
Prep 10 mins
Cook 35 mins

Ingredients
- 1 cup brown rice
- 2 chicken breasts
- 1 onion, diced
- 2 cups stock

Method
1. Brown chicken and set aside.
2. Fry onion.
3. Add rice and stock.
4. Return chicken and simmer until cooked.
```

---

## 5) Review/Edit-Before-Save Flow

Manual checks on suggestion detail:
- [x] **Edit Before Save** is available for `draft`/`draft_invalid`
- [x] Edit form allows updating title, metadata, ingredients, method, notes
- [x] Save suggestion edits returns to suggestion detail with updated content
- [x] After edits, suggestion can be accepted to recipe library

---

## 6) Accept/Reject Suggestion Actions

Manual checks:
- [x] **Save to Recipe Library** works for `draft` suggestions
- [x] Accepted suggestion status changes to `accepted`
- [x] Recipe appears in `/recipes` and opens correctly
- [x] **Reject Suggestion** changes status to `rejected`
- [x] Rejected suggestion no longer shows save action

---

## 7) End-to-End Lifecycle Scenarios

### Scenario A: Generate -> Review -> Edit -> Save
- [x] Generate recipe from `/generate`
- [x] Review in `/suggestions/<id>`
- [x] Edit with **Edit Before Save**
- [x] Save to recipe library
- [x] Confirm in `/recipes` and detail page

### Scenario B: Import Raw -> Review -> Save
- [x] Import raw recipe via `/import`
- [x] Review converted suggestion
- [x] Save to recipe library
- [x] Confirm in `/recipes`

### Scenario C: Edit Existing -> Delete
- [x] Edit a saved recipe and confirm updates
- [x] Delete it and confirm it disappears from list

---

## 8) Regression Test Suite

Run:

```bash
.venv/bin/python -m unittest tests.test_web_routes tests.test_conversion_service -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall app tests run.py
```

Checks:
- [x] Web route lifecycle tests pass
- [x] Conversion tests pass
- [x] Full suite passes
- [x] Compile check passes

---

## 9) Validation Gate Decision

Gate requirement: user can edit, delete, import, and save multiple recipes reliably.

Overall Result:
- [x] PASS - Phase 5 validation gate complete
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
