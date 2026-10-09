from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...extensions import get_mongo_db
from ...repositories import RecipesRepository, SuggestionsRepository
from ...services import MEAL_TYPES, generate_recipe_suggestion


web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def index() -> str:
    db = get_mongo_db()
    recipes_repo = RecipesRepository(db)
    suggestions_repo = SuggestionsRepository(db)

    recipes_count = len(recipes_repo.list(limit=500))
    draft_count = len(suggestions_repo.list_by_status("draft", limit=500))
    invalid_count = len(suggestions_repo.list_by_status("draft_invalid", limit=500))

    return render_template(
        "dashboard.html",
        recipes_count=recipes_count,
        draft_count=draft_count,
        invalid_count=invalid_count,
    )


@web_bp.route("/generate", methods=["GET", "POST"])
def generate_page() -> str:
    selected_meal_type = "main"
    instructions = ""
    model_override = ""

    if request.method == "POST":
        selected_meal_type = str(request.form.get("meal_type", "main")).strip()
        instructions = str(request.form.get("instructions", "")).strip()
        model_override = str(request.form.get("model", "")).strip()

        if selected_meal_type not in MEAL_TYPES:
            flash("Please select a valid meal type.", "danger")
            return redirect(url_for("web.generate_page"))

        try:
            result = generate_recipe_suggestion(
                db=get_mongo_db(),
                meal_type=selected_meal_type,
                instructions=instructions,
                model_override=model_override or None,
            )
        except Exception:
            flash(
                "Generation is temporarily unavailable because the database connection failed. "
                "Please verify MongoDB Atlas connectivity and try again.",
                "danger",
            )
            return redirect(url_for("web.generate_page"))

        if not result.get("ok"):
            flash(result.get("error", "Generation failed."), "danger")
            return redirect(url_for("web.generate_page"))

        if result.get("status") == "draft":
            flash("Recipe suggestion generated. Review and save it to your library.", "success")
        else:
            flash("Suggestion generated but marked draft_invalid. Review details before saving.", "warning")

        return redirect(url_for("web.suggestion_detail", suggestion_id=result["suggestion_id"]))

    return render_template(
        "generate.html",
        meal_types=sorted(MEAL_TYPES),
        selected_meal_type=selected_meal_type,
        instructions=instructions,
        model_override=model_override,
    )


@web_bp.get("/suggestions")
def suggestions_page() -> str:
    status = str(request.args.get("status", "draft")).strip()
    repo = SuggestionsRepository(get_mongo_db())

    if status == "all":
        suggestions = []
        for value in ["draft", "draft_invalid", "accepted", "rejected"]:
            suggestions.extend(repo.list_by_status(value, limit=200))
        suggestions = sorted(suggestions, key=lambda item: item.get("created_at"), reverse=True)
    else:
        suggestions = repo.list_by_status(status, limit=200)

    return render_template("suggestions.html", suggestions=suggestions, selected_status=status)


@web_bp.get("/suggestions/<suggestion_id>")
def suggestion_detail(suggestion_id: str) -> str:
    suggestion = SuggestionsRepository(get_mongo_db()).get_by_id(suggestion_id)
    if not suggestion:
        flash("Suggestion not found.", "warning")
        return redirect(url_for("web.suggestions_page"))
    return render_template("suggestion_detail.html", suggestion=suggestion)


@web_bp.post("/suggestions/<suggestion_id>/accept")
def accept_suggestion(suggestion_id: str):
    db = get_mongo_db()
    suggestions_repo = SuggestionsRepository(db)
    recipes_repo = RecipesRepository(db)

    suggestion = suggestions_repo.get_by_id(suggestion_id)
    if not suggestion:
        flash("Suggestion not found.", "warning")
        return redirect(url_for("web.suggestions_page"))

    if suggestion.get("status") != "draft":
        flash("Only draft suggestions can be saved.", "warning")
        return redirect(url_for("web.suggestion_detail", suggestion_id=suggestion_id))

    payload = suggestion.get("recipe", {})
    metadata = payload.get("metadata", {})

    try:
        recipe = recipes_repo.create(
            {
                "title": payload.get("title", suggestion.get("title", "Untitled")),
                "meal_type": payload.get("meal_type", suggestion.get("meal_type", "main")),
                "source_type": payload.get("source_type", "ai"),
                "source": metadata.get("source", "AI Generated"),
                "servings": metadata.get("servings", ""),
                "prep_time": metadata.get("prep_time", ""),
                "cook_time": metadata.get("cook_time", ""),
                "rating": metadata.get("rating", ""),
                "difficulty": metadata.get("difficulty", ""),
                "tags": metadata.get("tags", []),
                "ingredients": payload.get("ingredients", []),
                "method": payload.get("method", []),
                "notes": payload.get("notes", []),
            }
        )
    except Exception:
        flash("Could not save this suggestion due to a database constraint. Please try again.", "danger")
        return redirect(url_for("web.suggestion_detail", suggestion_id=suggestion_id))

    suggestions_repo.update_status(suggestion_id, "accepted")
    flash("Suggestion saved to recipe library.", "success")
    return redirect(url_for("web.recipe_detail", recipe_id=str(recipe["_id"])))


@web_bp.post("/suggestions/<suggestion_id>/reject")
def reject_suggestion(suggestion_id: str):
    updated = SuggestionsRepository(get_mongo_db()).update_status(suggestion_id, "rejected")
    if updated:
        flash("Suggestion rejected.", "info")
    else:
        flash("Suggestion not found.", "warning")
    return redirect(url_for("web.suggestions_page"))


@web_bp.get("/recipes")
def recipes_page() -> str:
    selected_meal_type = str(request.args.get("meal_type", "")).strip()
    if selected_meal_type and selected_meal_type not in MEAL_TYPES:
        selected_meal_type = ""
        flash("Invalid meal type filter ignored.", "warning")

    recipes = RecipesRepository(get_mongo_db()).list(meal_type=selected_meal_type or None, limit=300)
    return render_template(
        "recipes.html",
        recipes=recipes,
        meal_types=sorted(MEAL_TYPES),
        selected_meal_type=selected_meal_type,
    )


@web_bp.get("/recipes/<recipe_id>")
def recipe_detail(recipe_id: str) -> str:
    recipe = RecipesRepository(get_mongo_db()).get_by_id(recipe_id)
    if not recipe:
        flash("Recipe not found.", "warning")
        return redirect(url_for("web.recipes_page"))

    return render_template("recipe_detail.html", recipe=recipe)
