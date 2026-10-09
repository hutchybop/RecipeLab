from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import AppConfig
from app.repositories import RecipesRepository, ensure_all_indexes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import markdown recipes into MongoDB")
    parser.add_argument(
        "--recipes-dir", default="recipes", help="Path to markdown recipes directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without writing to MongoDB",
    )
    return parser.parse_args()


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, Any], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0

    metadata: dict[str, Any] = {}
    idx = 1
    while idx < len(lines):
        line = lines[idx].strip()
        if line == "---":
            return metadata, idx + 1
        if ":" not in line:
            idx += 1
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value.startswith("[") and value.endswith("]"):
            values = [part.strip() for part in value[1:-1].split(",") if part.strip()]
            metadata[key] = values
        else:
            metadata[key] = value
        idx += 1

    return metadata, idx


def parse_markdown_recipe(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata, start_idx = parse_frontmatter(lines)

    current_section = ""
    ingredients: list[str] = []
    method: list[str] = []
    notes: list[str] = []

    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            current_section = stripped[3:].strip().lower()
            continue

        if current_section == "ingredients":
            ingredients.append(stripped.lstrip("- ").strip())
        elif current_section == "method":
            step = re.sub(r"^\d+\.\s*", "", stripped)
            method.append(step)
        elif current_section == "notes":
            notes.append(stripped.lstrip("- ").strip())

    return {
        "title": metadata.get("title", path.stem),
        "source": metadata.get("source", ""),
        "servings": metadata.get("servings", ""),
        "prep_time": metadata.get("prep_time", ""),
        "cook_time": metadata.get("cook_time", ""),
        "rating": metadata.get("rating", ""),
        "difficulty": metadata.get("difficulty", ""),
        "tags": metadata.get("tags", []),
        "ingredients": ingredients,
        "method": method,
        "notes": notes,
    }


def infer_meal_type(recipe_file: Path) -> str:
    normalized = recipe_file.as_posix().lower()
    if "/recipes/main/" in normalized or "/recipes/ai-suggested/main/" in normalized:
        return "main"
    if (
        "/recipes/lunch/weekday (batch)/" in normalized
        or "/recipes/ai-suggested/lunch-batch/" in normalized
    ):
        return "lunch_batch"
    if "/recipes/lunch/weekend/" in normalized:
        return "lunch_single"
    if "/recipes/dessert/" in normalized:
        return "dessert"
    return "main"


def infer_source_type(recipe_file: Path) -> str:
    return (
        "ai" if "/recipes/ai-suggested/" in recipe_file.as_posix().lower() else "user"
    )


def main() -> int:
    args = parse_args()
    config = AppConfig.from_env()
    if not args.dry_run:
        missing = config.validate()
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variables: {joined}")

    recipes_root = Path(args.recipes_dir).resolve()
    recipe_files = sorted(recipes_root.rglob("*.md"))

    if args.dry_run:
        repository = None
    else:
        mongo_client = MongoClient(config.mongo_uri)
        db = mongo_client[config.mongo_db_name]
        ensure_all_indexes(db)
        repository = RecipesRepository(db)

    imported_count = 0
    for recipe_file in recipe_files:
        recipe_payload = parse_markdown_recipe(recipe_file)
        recipe_payload["meal_type"] = infer_meal_type(recipe_file)
        recipe_payload["source_type"] = infer_source_type(recipe_file)
        source_path = str(recipe_file.relative_to(Path.cwd()))

        if repository is not None:
            repository.upsert_by_source_path(
                source_path=source_path, document=recipe_payload
            )

        imported_count += 1

    mode = "dry-run" if args.dry_run else "import"
    print(f"{mode} complete: {imported_count} recipes processed from {recipes_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
