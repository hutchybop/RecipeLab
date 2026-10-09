from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...extensions import get_mongo_db
from ...repositories import RecipesRepository, SuggestionsRepository
from ...services import MEAL_TYPES, convert_raw_recipe_to_suggestion, generate_recipe_suggestion, normalize_recipe_document


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


@web_bp.route("/suggestions/<suggestion_id>/edit", methods=["GET", "POST"])
def edit_suggestion(suggestion_id: str):
    repo = SuggestionsRepository(get_mongo_db())
    suggestion = repo.get_by_id(suggestion_id)
    if not suggestion:
        flash("Suggestion not found.", "warning")
        return redirect(url_for("web.suggestions_page"))

    if suggestion.get("status") not in {"draft", "draft_invalid"}:
        flash("Only draft suggestions can be edited.", "warning")
        return redirect(url_for("web.suggestion_detail", suggestion_id=suggestion_id))

    if request.method == "POST":
        meal_type = str(request.form.get("meal_type", suggestion.get("meal_type", "main"))).strip()
        if meal_type not in MEAL_TYPES:
            flash("Please select a valid meal type.", "danger")
            return redirect(url_for("web.edit_suggestion", suggestion_id=suggestion_id))

        tags = [item.strip() for item in str(request.form.get("tags", "")).split(",") if item.strip()]
        method = [item.strip() for item in str(request.form.get("method", "")).splitlines() if item.strip()]
        notes = [item.strip() for item in str(request.form.get("notes", "")).splitlines() if item.strip()]
        ingredients_lines = [item.strip() for item in str(request.form.get("ingredients", "")).splitlines() if item.strip()]

        recipe_payload = {
            "title": str(request.form.get("title", "")).strip(),
            "meal_type": meal_type,
            "source_type": str(request.form.get("source_type", "user")).strip() or "user",
            "source": str(request.form.get("source", "")).strip(),
            "servings": str(request.form.get("servings", "")).strip(),
            "prep_time": str(request.form.get("prep_time", "")).strip(),
            "cook_time": str(request.form.get("cook_time", "")).strip(),
            "rating": str(request.form.get("rating", "")).strip(),
            "difficulty": str(request.form.get("difficulty", "")).strip(),
            "tags": tags,
            "ingredients": ingredients_lines,
            "method": method,
            "notes": notes,
        }

        try:
            normalized_recipe = normalize_recipe_document(recipe_payload)
            updated = repo.update_recipe_for_review(
                suggestion_id,
                title=recipe_payload["title"],
                meal_type=meal_type,
                recipe=normalized_recipe,
            )
        except Exception as exc:
            flash(f"Could not update suggestion: {exc}", "danger")
            return redirect(url_for("web.edit_suggestion", suggestion_id=suggestion_id))

        if updated:
            flash("Suggestion updated. Review and save when ready.", "success")
        else:
            flash("No changes were saved.", "warning")
        return redirect(url_for("web.suggestion_detail", suggestion_id=suggestion_id))

    return render_template("suggestion_edit.html", suggestion=suggestion, meal_types=sorted(MEAL_TYPES))


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


@web_bp.route("/import", methods=["GET", "POST"])
def import_recipe_page() -> str:
    selected_meal_type = "main"
    raw_recipe_text = ""
    model_override = ""

    if request.method == "POST":
        selected_meal_type = str(request.form.get("meal_type", "main")).strip()
        raw_recipe_text = str(request.form.get("raw_recipe_text", "")).strip()
        model_override = str(request.form.get("model", "")).strip()

        if selected_meal_type not in MEAL_TYPES:
            flash("Please select a valid meal type.", "danger")
            return redirect(url_for("web.import_recipe_page"))

        if not raw_recipe_text:
            flash("Please paste a raw recipe to convert.", "warning")
            return redirect(url_for("web.import_recipe_page"))

        try:
            result = convert_raw_recipe_to_suggestion(
                db=get_mongo_db(),
                meal_type=selected_meal_type,
                raw_recipe_text=raw_recipe_text,
                model_override=model_override or None,
            )
        except Exception:
            flash(
                "Recipe conversion is temporarily unavailable because the database connection failed.",
                "danger",
            )
            return redirect(url_for("web.import_recipe_page"))

        if not result.get("ok"):
            flash(result.get("error", "Conversion failed."), "danger")
            return redirect(url_for("web.import_recipe_page"))

        if result.get("status") == "draft":
            flash("Raw recipe converted. Review and save it to your library.", "success")
        else:
            flash("Converted output failed validation. Review and edit before saving.", "warning")

        return redirect(url_for("web.suggestion_detail", suggestion_id=result["suggestion_id"]))

    return render_template(
        "import_recipe.html",
        meal_types=sorted(MEAL_TYPES),
        selected_meal_type=selected_meal_type,
        raw_recipe_text=raw_recipe_text,
        model_override=model_override,
    )


@web_bp.get("/recipes/<recipe_id>")
def recipe_detail(recipe_id: str) -> str:
    recipe = RecipesRepository(get_mongo_db()).get_by_id(recipe_id)
    if not recipe or recipe.get("deleted_at") is not None:
        flash("Recipe not found.", "warning")
        return redirect(url_for("web.recipes_page"))

    return render_template("recipe_detail.html", recipe=recipe)


@web_bp.route("/recipes/<recipe_id>/edit", methods=["GET", "POST"])
def edit_recipe(recipe_id: str):
    repo = RecipesRepository(get_mongo_db())
    recipe = repo.get_by_id(recipe_id)
    if not recipe or recipe.get("deleted_at") is not None:
        flash("Recipe not found.", "warning")
        return redirect(url_for("web.recipes_page"))

    if request.method == "POST":
        meal_type = str(request.form.get("meal_type", recipe.get("meal_type", "main"))).strip()
        if meal_type not in MEAL_TYPES:
            flash("Please select a valid meal type.", "danger")
            return redirect(url_for("web.edit_recipe", recipe_id=recipe_id))

        tags = [item.strip() for item in str(request.form.get("tags", "")).split(",") if item.strip()]
        method = [item.strip() for item in str(request.form.get("method", "")).splitlines() if item.strip()]
        notes = [item.strip() for item in str(request.form.get("notes", "")).splitlines() if item.strip()]

        ingredients_lines = [item.strip() for item in str(request.form.get("ingredients", "")).splitlines() if item.strip()]

        update_fields = {
            "title": str(request.form.get("title", "")).strip(),
            "meal_type": meal_type,
            "source_type": str(request.form.get("source_type", recipe.get("source_type", "user"))).strip() or "user",
            "ingredients": ingredients_lines,
            "method": method,
            "notes": notes,
            "source": str(request.form.get("source", "")).strip(),
            "servings": str(request.form.get("servings", "")).strip(),
            "prep_time": str(request.form.get("prep_time", "")).strip(),
            "cook_time": str(request.form.get("cook_time", "")).strip(),
            "rating": str(request.form.get("rating", "")).strip(),
            "difficulty": str(request.form.get("difficulty", "")).strip(),
            "tags": tags,
        }

        try:
            updated = repo.update(recipe_id, update_fields)
        except Exception as exc:
            flash(f"Could not update recipe: {exc}", "danger")
            return redirect(url_for("web.edit_recipe", recipe_id=recipe_id))

        if updated:
            flash("Recipe updated.", "success")
        else:
            flash("No changes were saved.", "warning")
        return redirect(url_for("web.recipe_detail", recipe_id=recipe_id))

    return render_template("recipe_edit.html", recipe=recipe, meal_types=sorted(MEAL_TYPES))


@web_bp.post("/recipes/<recipe_id>/delete")
def delete_recipe(recipe_id: str):
    deleted = RecipesRepository(get_mongo_db()).soft_delete(recipe_id)
    if deleted:
        flash("Recipe deleted.", "info")
    else:
        flash("Recipe not found.", "warning")
    return redirect(url_for("web.recipes_page"))
