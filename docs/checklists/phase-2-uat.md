# Phase 2 UAT Checklist - Data Model and Repositories

Date: 26-10-08
Tester: hutch
Environment/Branch: .venv main
Mongo DB Name Used: RecipeLab_phase2_uat

---

## 1) Preconditions

- [ ] `.env` is present and contains `SECRET_KEY` and `MONGO_URI`
- [ ] Using a dedicated validation DB name (recommended), e.g. `RecipeLab_phase2_uat`
- [ ] Virtual environment is active or `.venv/bin/python` is available

Optional `.env` setting:

```env
MONGO_DB_NAME=RecipeLab_phase2_uat
```

---

## 2) Run Real Import

Command:

```bash
.venv/bin/python scripts/import_markdown_recipes.py
```

Record output:

```
import complete: 44 recipes processed from /Users/hutch/Coding/RecipeLab/recipes
```

Checks:
- [x] Import completed without error
- [x] Reported processed count is reasonable for current `recipes/` contents

---

## 3) Validate Data Shape and Usability

Command:

```bash
.venv/bin/python - <<'PY'
from app.config import AppConfig
from pymongo import MongoClient

cfg = AppConfig.from_env()
client = MongoClient(cfg.mongo_uri)
db = client[cfg.mongo_db_name]

recipes = db["recipes"]
print("recipes count:", recipes.count_documents({}))

print("meal_type breakdown:")
for mt in ["main","lunch_batch","lunch_single","breakfast","dessert"]:
    print(" ", mt, recipes.count_documents({"meal_type": mt}))

print("source_type breakdown:")
for st in ["user","ai"]:
    print(" ", st, recipes.count_documents({"source_type": st}))

invalid = recipes.count_documents({
    "$or": [
        {"title": {"$in": [None, ""]}},
        {"ingredients": {"$size": 0}},
        {"method": {"$size": 0}},
        {"meal_type": {"$nin": ["main","lunch_batch","lunch_single","breakfast","dessert"]}},
    ]
})
print("invalid-shape docs:", invalid)

print("\nSample docs:")
for d in recipes.find({}, {"title":1,"meal_type":1,"source_type":1,"metadata.tags":1}).limit(5):
    print(d)
PY
```

Record output:

```
recipes count: 44
meal_type breakdown:
  main 29
  lunch_batch 10
  lunch_single 4
  breakfast 0
  dessert 1
source_type breakdown:
  user 37
  ai 7
invalid-shape docs: 0

Sample docs:
{'_id': ObjectId('6ac7d8e3e849f051b8352167'), 'meal_type': 'main', 'metadata': {'tags': ['dinner', 'weekday', 'vegetarian', 'lentils', 'indian-inspired', 'spicy', 'one-pot', 'high-protein', 'comforting']}, 'source_type': 'ai', 'title': 'Lentil and Tomato Curry with Spinach'}
{'_id': ObjectId('6ac7d8e3e849f051b8352168'), 'meal_type': 'main', 'metadata': {'tags': ['dinner', 'weekday', 'salmon', 'miso', 'asian-inspired', 'one-pan', 'healthy', 'high-protein', 'easy']}, 'source_type': 'ai', 'title': 'Miso Salmon with Roasted Vegetables'}
{'_id': ObjectId('6ac7d8e3e849f051b8352169'), 'meal_type': 'main', 'metadata': {'tags': ['dinner', 'weekday', 'chicken', 'legumes','spicy', 'asian-inspired', 'one-pan', 'high-protein', 'quick']}, 'source_type': 'ai', 'title': 'Spicy Black Bean and Chicken Stir-Fry'}
{'_id': ObjectId('6ac7d8e3e849f051b835216a'), 'meal_type': 'lunch_batch', 'metadata': {'tags': ['weekday', 'batch-cook', 'lunch', 'meal-prep', 'vegetarian', 'mediterranean', 'cold-salad', 'high-protein', 'beans', 'healthy']}, 'source_type': 'ai', 'title': 'Mediterranean White Bean and Herb Grain Bowl (x5)'}
{'_id': ObjectId('6ac7d8e3e849f051b835216b'), 'meal_type': 'lunch_batch', 'metadata': {'tags': ['weekday', 'batch-cook', 'lunch', 'meal-prep', 'chicken', 'asian-inspired', 'cold-salad', 'high-protein', 'miso', 'healthy']}, 'source_type': 'ai', 'title': 'Miso-Glazed Chicken and Edamame Power Salad (x5)'}
```

Pass criteria:
- [x] Recipe count is non-zero
- [x] Meal type distribution looks sensible
- [x] Source type distribution looks sensible
- [x] `invalid-shape docs` is `0`
- [x] Sample docs appear usable for downstream phases

---

## 4) Validate Indexes Exist

Command:

```bash
.venv/bin/python - <<'PY'
from app.config import AppConfig
from pymongo import MongoClient

cfg = AppConfig.from_env()
db = MongoClient(cfg.mongo_uri)[cfg.mongo_db_name]

for name in ["recipes","suggestions","preferences","feedback_events","generation_runs"]:
    print(f"\n{name} indexes:")
    for idx in db[name].list_indexes():
        print(" ", idx["name"])
PY
```

Record output:

```
recipes indexes:
  _id_
  recipes_meal_type_created_at
  recipes_source_type_created_at
  recipes_title
  recipes_deleted_at
  recipes_source_path_unique

suggestions indexes:
  _id_
  suggestions_status_created_at
  suggestions_meal_type_created_at
  suggestions_generation_run_id

preferences indexes:
  _id_
  preferences_profile_name_unique
  preferences_active

feedback_events indexes:
  _id_
  feedback_target_created_at
  feedback_signal_created_at

generation_runs indexes:
  _id_
  generation_runs_status_created_at
  generation_runs_meal_type_created_at
  generation_runs_model_created_at
```

Pass criteria:
- [x] `recipes` indexes present (including `recipes_source_path_unique`)
- [x] `suggestions` indexes present
- [x] `preferences` indexes present
- [x] `feedback_events` indexes present
- [x] `generation_runs` indexes present

---

## 5) Result and Sign-Off

Overall Result:
- [x] PASS - Phase 2 validation gate complete
- [ ] FAIL - remediation required

Notes / Issues Found:

```
N/A
```

Remediation Tasks (if any):

```
N/A
```

Sign-off:
- Name: hutch
- Date: 26-10-08
