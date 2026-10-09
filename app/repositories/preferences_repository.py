from __future__ import annotations

from typing import Any, Mapping

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from ..services.schema_utils import normalize_preference_document, utc_now


class PreferencesRepository:
    collection_name = "preferences"

    def __init__(self, db: Database):
        self.collection: Collection = db[self.collection_name]

    @classmethod
    def ensure_indexes(cls, db: Database) -> None:
        collection = db[cls.collection_name]
        collection.create_index(
            [("profile_name", ASCENDING)],
            unique=True,
            name="preferences_profile_name_unique",
        )
        collection.create_index([("active", ASCENDING)], name="preferences_active")

    def upsert_profile(self, document: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_preference_document(document)

        if normalized["active"]:
            self.collection.update_many(
                {"active": True}, {"$set": {"active": False, "updated_at": utc_now()}}
            )

        self.collection.update_one(
            {"profile_name": normalized["profile_name"]},
            {
                "$set": {
                    "active": normalized["active"],
                    "hard_avoids": normalized["hard_avoids"],
                    "likes": normalized["likes"],
                    "dislikes": normalized["dislikes"],
                    "notes": normalized["notes"],
                    "weights": normalized["weights"],
                    "updated_at": normalized["updated_at"],
                },
                "$setOnInsert": {"created_at": normalized["created_at"]},
            },
            upsert=True,
        )
        return normalized

    def get_active_profile(self) -> dict[str, Any] | None:
        return self.collection.find_one({"active": True})

    def list_profiles(self) -> list[dict[str, Any]]:
        return list(self.collection.find({}).sort("profile_name", ASCENDING))
