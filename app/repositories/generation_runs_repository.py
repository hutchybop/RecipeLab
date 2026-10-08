from __future__ import annotations

from typing import Any, Mapping

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from ..services.schema_utils import normalize_generation_run_document, normalize_generation_run_status, utc_now
from .common import to_object_id


class GenerationRunsRepository:
    collection_name = "generation_runs"

    def __init__(self, db: Database):
        self.collection: Collection = db[self.collection_name]

    @classmethod
    def ensure_indexes(cls, db: Database) -> None:
        collection = db[cls.collection_name]
        collection.create_index(
            [("status", ASCENDING), ("created_at", DESCENDING)],
            name="generation_runs_status_created_at",
        )
        collection.create_index(
            [("meal_type", ASCENDING), ("created_at", DESCENDING)],
            name="generation_runs_meal_type_created_at",
        )
        collection.create_index(
            [("model", ASCENDING), ("created_at", DESCENDING)],
            name="generation_runs_model_created_at",
        )

    def create(self, document: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_generation_run_document(document)
        result = self.collection.insert_one(normalized)
        normalized["_id"] = result.inserted_id
        return normalized

    def get_by_id(self, run_id: Any) -> dict[str, Any] | None:
        return self.collection.find_one({"_id": to_object_id(run_id)})

    def update_status(self, run_id: Any, status: str, *, raw_response: str = "", error: str = "") -> bool:
        normalized_status = normalize_generation_run_status(status)
        result = self.collection.update_one(
            {"_id": to_object_id(run_id)},
            {
                "$set": {
                    "status": normalized_status,
                    "raw_response": raw_response,
                    "error": error,
                    "updated_at": utc_now(),
                }
            },
        )
        return result.modified_count > 0
