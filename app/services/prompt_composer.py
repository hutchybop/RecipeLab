from __future__ import annotations

from typing import Any, Mapping


DEFAULT_HARD_CONSTRAINTS = [
    "whole chickpeas",
    "peanuts",
    "sprouts",
    "cauliflower",
    "cinnamon",
]


def compose_recipe_prompt(
    *,
    meal_type: str,
    instructions: str,
    profile: Mapping[str, Any] | None,
    hard_constraints: list[str] | None = None,
) -> str:
    profile = profile or {}
    constraints = hard_constraints or DEFAULT_HARD_CONSTRAINTS

    likes = ", ".join(profile.get("likes", [])) or "(none provided)"
    dislikes = ", ".join(profile.get("dislikes", [])) or "(none provided)"
    avoids = ", ".join(profile.get("hard_avoids", constraints))
    notes = profile.get("notes", "") or "(none provided)"
    user_instructions = instructions.strip() or "(none provided)"

    return (
        "Generate exactly one recipe as valid JSON only. No markdown, no extra prose.\n\n"
        f"Meal type: {meal_type}\n"
        f"User instructions: {user_instructions}\n\n"
        "Active tasting profile:\n"
        f"- likes: {likes}\n"
        f"- dislikes: {dislikes}\n"
        f"- hard avoids (strict): {avoids}\n"
        f"- notes: {notes}\n\n"
        "Hard requirements:\n"
        "- Respect all hard avoids strictly.\n"
        "- Keep difficulty practical for a home cook.\n"
        "- Include at least one clear protein source.\n"
        "- Keep method concise and sequential.\n\n"
        "Output JSON object schema:\n"
        "{\n"
        '  "title": "string",\n'
        '  "meal_type": "string",\n'
        '  "source": "AI Generated",\n'
        '  "servings": "string or number",\n'
        '  "prep_time": "string or number",\n'
        '  "cook_time": "string or number",\n'
        '  "rating": "string or number",\n'
        '  "difficulty": "string or number",\n'
        '  "tags": ["string"],\n'
        '  "ingredients": [{"quantity": "string", "unit": "string", "ingredient": "string"}],\n'
        '  "method": ["string"],\n'
        '  "notes": ["string"]\n'
        "}\n"
    )
