from __future__ import annotations

from typing import Any, Mapping

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from ..services.schema_utils import normalize_suggestion_document, utc_now
from .common import to_object_id


class SuggestionsRepository:
    collection_name = "suggestions"

    def __init__(self, db: Database):
        self.collection: Collection = db[self.collection_name]

    @classmethod
    def ensure_indexes(cls, db: Database) -> None:
        collection = db[cls.collection_name]
        collection.create_index(
            [("status", ASCENDING), ("created_at", DESCENDING)],
            name="suggestions_status_created_at",
        )
        collection.create_index(
            [("meal_type", ASCENDING), ("created_at", DESCENDING)],
            name="suggestions_meal_type_created_at",
        )
        collection.create_index(
            [("generation_run_id", ASCENDING)], name="suggestions_generation_run_id"
        )

    def create(self, document: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_suggestion_document(document)
        insert_result = self.collection.insert_one(normalized)
        normalized["_id"] = insert_result.inserted_id
        return normalized

    def get_by_id(self, suggestion_id: Any) -> dict[str, Any] | None:
        return self.collection.find_one({"_id": to_object_id(suggestion_id)})

    def list_by_status(self, status: str, *, limit: int = 100) -> list[dict[str, Any]]:
        cursor = (
            self.collection.find({"status": status})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return list(cursor)

    def update_status(self, suggestion_id: Any, status: str) -> bool:
        result = self.collection.update_one(
            {"_id": to_object_id(suggestion_id)},
            {"$set": {"status": status, "updated_at": utc_now()}},
        )
        return result.modified_count > 0

    def update_recipe_for_review(
        self, suggestion_id: Any, *, title: str, meal_type: str, recipe: dict[str, Any]
    ) -> bool:
        result = self.collection.update_one(
            {"_id": to_object_id(suggestion_id)},
            {
                "$set": {
                    "title": title,
                    "meal_type": meal_type,
                    "recipe": recipe,
                    "validation": {"valid": True, "errors": []},
                    "status": "draft",
                    "updated_at": utc_now(),
                }
            },
        )
        return result.modified_count > 0
