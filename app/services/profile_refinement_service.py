from __future__ import annotations

import re
from collections import Counter
from typing import Any

from pymongo.database import Database

from ..repositories import (
    FeedbackEventsRepository,
    PreferencesRepository,
    ProfileUpdateSuggestionsRepository,
    RecipesRepository,
    SuggestionsRepository,
)

_TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z\-]{2,}")
_STOPWORDS = {
    "fresh",
    "large",
    "small",
    "taste",
    "optional",
    "minutes",
    "minute",
    "tablespoon",
    "teaspoon",
    "cups",
    "cup",
}


def generate_profile_update_suggestions(db: Database, *, min_support: int = 2, limit: int = 300) -> dict[str, Any]:
    feedback_repo = FeedbackEventsRepository(db)
    preferences_repo = PreferencesRepository(db)
    profile_updates_repo = ProfileUpdateSuggestionsRepository(db)
    recipes_repo = RecipesRepository(db)
    suggestions_repo = SuggestionsRepository(db)

    active_profile = preferences_repo.get_active_profile() or {
        "profile_name": "default",
        "active": True,
        "hard_avoids": [],
        "likes": [],
        "dislikes": [],
        "notes": "",
        "weights": {},
    }

    liked_counts: Counter[str] = Counter()
    disliked_counts: Counter[str] = Counter()

    events = feedback_repo.list_recent(limit=limit)
    for event in events:
        signal = event.get("signal")
        if signal not in {"liked", "disliked"}:
            continue

        target_recipe = _resolve_target_recipe(
            event=event,
            recipes_repo=recipes_repo,
            suggestions_repo=suggestions_repo,
        )
        if not target_recipe:
            continue

        tokens = _extract_tokens(target_recipe)
        if signal == "liked":
            liked_counts.update(tokens)
        else:
            disliked_counts.update(tokens)

    existing_pending = {(item.get("action"), item.get("token")) for item in profile_updates_repo.list_pending(limit=500)}
    likes = {str(item).lower() for item in active_profile.get("likes", [])}
    dislikes = {str(item).lower() for item in active_profile.get("dislikes", [])}
    hard_avoids = {str(item).lower() for item in active_profile.get("hard_avoids", [])}

    created = 0
    for token, count in liked_counts.items():
        if count < min_support:
            continue
        if token in likes or token in dislikes or token in hard_avoids:
            continue
        key = ("add_like", token)
        if key in existing_pending:
            continue
        profile_updates_repo.create(
            {
                "action": "add_like",
                "token": token,
                "support_count": count,
                "status": "pending",
                "notes": f"Observed in {count} liked feedback events.",
            }
        )
        existing_pending.add(key)
        created += 1

    for token, count in disliked_counts.items():
        if count < min_support:
            continue
        if token in dislikes or token in likes or token in hard_avoids:
            continue
        key = ("add_dislike", token)
        if key in existing_pending:
            continue
        profile_updates_repo.create(
            {
                "action": "add_dislike",
                "token": token,
                "support_count": count,
                "status": "pending",
                "notes": f"Observed in {count} disliked feedback events.",
            }
        )
        existing_pending.add(key)
        created += 1

    return {"created": created, "pending_total": len(profile_updates_repo.list_pending(limit=500))}


def apply_profile_update_suggestion(db: Database, suggestion_id: str) -> tuple[bool, str]:
    profile_updates_repo = ProfileUpdateSuggestionsRepository(db)
    preferences_repo = PreferencesRepository(db)

    suggestion = profile_updates_repo.get_by_id(suggestion_id)
    if not suggestion:
        return False, "Suggestion not found"
    if suggestion.get("status") != "pending":
        return False, "Suggestion is not pending"

    profile = preferences_repo.get_active_profile() or {
        "profile_name": "default",
        "active": True,
        "hard_avoids": [],
        "likes": [],
        "dislikes": [],
        "notes": "",
        "weights": {},
    }
    token = str(suggestion.get("token", "")).strip().lower()
    action = suggestion.get("action")

    likes = [str(item).strip() for item in profile.get("likes", []) if str(item).strip()]
    dislikes = [str(item).strip() for item in profile.get("dislikes", []) if str(item).strip()]
    hard_avoids = [str(item).strip() for item in profile.get("hard_avoids", []) if str(item).strip()]

    if action == "add_like" and token and token not in {item.lower() for item in likes}:
        likes.append(token)
        dislikes = [item for item in dislikes if item.lower() != token]
    elif action == "add_dislike" and token and token not in {item.lower() for item in hard_avoids}:
        dislikes.append(token)
        likes = [item for item in likes if item.lower() != token]
    else:
        return False, "No applicable change"

    preferences_repo.upsert_profile(
        {
            "profile_name": profile.get("profile_name", "default"),
            "active": True,
            "hard_avoids": hard_avoids,
            "likes": likes,
            "dislikes": dislikes,
            "notes": profile.get("notes", ""),
            "weights": profile.get("weights", {}),
        }
    )
    profile_updates_repo.update_status(suggestion_id, "applied")
    return True, "Profile updated"


def reject_profile_update_suggestion(db: Database, suggestion_id: str) -> bool:
    return ProfileUpdateSuggestionsRepository(db).update_status(suggestion_id, "rejected")


def _resolve_target_recipe(*, event: dict[str, Any], recipes_repo: RecipesRepository, suggestions_repo: SuggestionsRepository) -> dict[str, Any] | None:
    target_type = event.get("target_type")
    target_id = event.get("target_id")
    if not target_id:
        return None

    if target_type == "recipe":
        return recipes_repo.get_by_id(target_id)
    if target_type == "suggestion":
        suggestion = suggestions_repo.get_by_id(target_id)
        if suggestion:
            return suggestion.get("recipe")
    return None


def _extract_tokens(recipe: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    metadata = recipe.get("metadata", {}) if isinstance(recipe, dict) else {}

    for tag in metadata.get("tags", []) if isinstance(metadata, dict) else []:
        clean = str(tag).strip().lower()
        if clean and clean not in _STOPWORDS:
            tokens.add(clean)

    for ingredient in recipe.get("ingredients", []) if isinstance(recipe, dict) else []:
        name = ""
        if isinstance(ingredient, dict):
            name = str(ingredient.get("ingredient", ""))
        elif isinstance(ingredient, str):
            name = ingredient
        for match in _TOKEN_PATTERN.findall(name.lower()):
            token = match.strip()
            if token and token not in _STOPWORDS:
                tokens.add(token)

    return tokens
