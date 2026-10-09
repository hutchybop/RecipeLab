from __future__ import annotations

import json
from typing import Any, Mapping

from flask import current_app
from pymongo.database import Database

from ..repositories import GenerationRunsRepository, PreferencesRepository, SuggestionsRepository, ensure_all_indexes
from .llm_adapter import LLMAdapter, LLMAdapterError
from .prompt_composer import compose_recipe_prompt
from .schema_utils import normalize_recipe_document


def generate_recipe_suggestion(*, db: Database, meal_type: str, instructions: str, model_override: str | None = None) -> dict[str, Any]:
    ensure_all_indexes(db)

    generation_runs_repository = GenerationRunsRepository(db)
    suggestions_repository = SuggestionsRepository(db)
    preferences_repository = PreferencesRepository(db)

    profile = preferences_repository.get_active_profile() or {}
    model = (model_override or current_app.config.get("LLM_MODEL", "")).strip()
    provider = current_app.config.get("LLM_PROVIDER", "").strip()
    endpoint = current_app.config.get("LLM_ENDPOINT", "").strip()
    api_key = current_app.config.get("LLM_API_KEY", "").strip()

    if not provider or not model:
        return {
            "ok": False,
            "status_code": 503,
            "error": "Generation is not configured. Set LLM_PROVIDER and LLM_MODEL in .env.",
        }

    prompt = compose_recipe_prompt(
        meal_type=meal_type,
        instructions=instructions,
        profile=profile,
    )

    run = generation_runs_repository.create(
        {
            "meal_type": meal_type,
            "model": model,
            "provider": provider,
            "prompt": prompt,
            "status": "started",
        }
    )

    adapter = LLMAdapter(provider=provider, endpoint=endpoint, api_key=api_key, model=model)

    try:
        raw_response = adapter.generate_recipe(prompt)
    except LLMAdapterError as exc:
        generation_runs_repository.update_status(run["_id"], "failed", error=str(exc))
        return {
            "ok": False,
            "status_code": 502,
            "error": str(exc),
            "run_id": str(run["_id"]),
        }

    validation_errors: list[str] = []
    parsed_recipe = _parse_recipe_json(raw_response, validation_errors)

    suggestion_recipe: dict[str, Any]
    status: str
    if parsed_recipe is None:
        suggestion_recipe = {
            "meal_type": meal_type,
            "source_type": "ai",
            "raw_response": raw_response,
        }
        status = "draft_invalid"
    else:
        try:
            suggestion_recipe = normalize_recipe_document(
                {
                    "title": parsed_recipe.get("title", "Untitled suggestion"),
                    "meal_type": meal_type,
                    "source_type": "ai",
                    "source": parsed_recipe.get("source", "AI Generated"),
                    "servings": parsed_recipe.get("servings", ""),
                    "prep_time": parsed_recipe.get("prep_time", ""),
                    "cook_time": parsed_recipe.get("cook_time", ""),
                    "rating": parsed_recipe.get("rating", ""),
                    "difficulty": parsed_recipe.get("difficulty", ""),
                    "tags": parsed_recipe.get("tags", []),
                    "ingredients": parsed_recipe.get("ingredients", []),
                    "method": parsed_recipe.get("method", []),
                    "notes": parsed_recipe.get("notes", []),
                }
            )
            status = "draft"
        except ValueError as exc:
            validation_errors.append(str(exc))
            suggestion_recipe = {
                "meal_type": meal_type,
                "source_type": "ai",
                "raw_response": raw_response,
            }
            status = "draft_invalid"

    suggestion = suggestions_repository.create(
        {
            "title": parsed_recipe.get("title") if parsed_recipe else "Invalid suggestion output",
            "meal_type": meal_type,
            "status": status,
            "generation_run_id": str(run["_id"]),
            "validation": {
                "valid": status == "draft",
                "errors": validation_errors,
            },
            "recipe": suggestion_recipe,
        }
    )

    if status == "draft":
        generation_runs_repository.update_status(run["_id"], "succeeded", raw_response=raw_response)
    else:
        generation_runs_repository.update_status(
            run["_id"],
            "failed",
            raw_response=raw_response,
            error="; ".join(validation_errors) or "Invalid recipe output",
        )

    return {
        "ok": True,
        "status_code": 201 if status == "draft" else 422,
        "run_id": str(run["_id"]),
        "suggestion_id": str(suggestion["_id"]),
        "status": status,
        "validation": suggestion["validation"],
        "recipe": suggestion_recipe,
    }


def _parse_recipe_json(raw_response: str, errors: list[str]) -> Mapping[str, Any] | None:
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError:
        errors.append("LLM output was not valid JSON")
        return None

    if isinstance(payload, dict) and isinstance(payload.get("recipe"), dict):
        payload = payload["recipe"]

    if not isinstance(payload, dict):
        errors.append("LLM JSON output must be an object")
        return None

    return payload
