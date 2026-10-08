from __future__ import annotations

from typing import Any, Mapping

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from ..services.schema_utils import normalize_recipe_document, normalize_recipe_update, utc_now
from .common import to_object_id


class RecipesRepository:
    collection_name = "recipes"

    def __init__(self, db: Database):
        self.collection: Collection = db[self.collection_name]

    @classmethod
    def ensure_indexes(cls, db: Database) -> None:
        collection = db[cls.collection_name]
        collection.create_index(
            [("meal_type", ASCENDING), ("created_at", DESCENDING)],
            name="recipes_meal_type_created_at",
        )
        collection.create_index(
            [("source_type", ASCENDING), ("created_at", DESCENDING)],
            name="recipes_source_type_created_at",
        )
        collection.create_index([("title", ASCENDING)], name="recipes_title")
        collection.create_index([("deleted_at", ASCENDING)], name="recipes_deleted_at")
        collection.create_index(
            [("source_path", ASCENDING)],
            unique=True,
            sparse=True,
            name="recipes_source_path_unique",
        )

    def create(self, document: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_recipe_document(document)
        insert_result = self.collection.insert_one(normalized)
        normalized["_id"] = insert_result.inserted_id
        return normalized

    def get_by_id(self, recipe_id: Any) -> dict[str, Any] | None:
        return self.collection.find_one({"_id": to_object_id(recipe_id)})

    def list(self, *, meal_type: str | None = None, include_deleted: bool = False, limit: int = 100) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if meal_type:
            filters["meal_type"] = meal_type
        if not include_deleted:
            filters["deleted_at"] = None

        cursor = self.collection.find(filters).sort("created_at", DESCENDING).limit(limit)
        return list(cursor)

    def update(self, recipe_id: Any, update_fields: Mapping[str, Any]) -> bool:
        normalized_update = normalize_recipe_update(update_fields)
        result = self.collection.update_one(
            {"_id": to_object_id(recipe_id), "deleted_at": None},
            {"$set": normalized_update},
        )
        return result.modified_count > 0

    def soft_delete(self, recipe_id: Any) -> bool:
        result = self.collection.update_one(
            {"_id": to_object_id(recipe_id), "deleted_at": None},
            {"$set": {"deleted_at": utc_now(), "updated_at": utc_now()}},
        )
        return result.modified_count > 0

    def upsert_by_source_path(self, source_path: str, document: Mapping[str, Any]) -> None:
        normalized = normalize_recipe_document({**document, "source_path": source_path})
        created_at = normalized.pop("created_at")
        self.collection.update_one(
            {"source_path": source_path},
            {
                "$set": normalized,
                "$setOnInsert": {"created_at": created_at},
            },
            upsert=True,
        )
