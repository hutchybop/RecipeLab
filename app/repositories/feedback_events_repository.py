from __future__ import annotations

from typing import Any, Mapping

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from ..services.schema_utils import normalize_feedback_event_document


class FeedbackEventsRepository:
    collection_name = "feedback_events"

    def __init__(self, db: Database):
        self.collection: Collection = db[self.collection_name]

    @classmethod
    def ensure_indexes(cls, db: Database) -> None:
        collection = db[cls.collection_name]
        collection.create_index(
            [
                ("target_type", ASCENDING),
                ("target_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
            name="feedback_target_created_at",
        )
        collection.create_index(
            [("signal", ASCENDING), ("created_at", DESCENDING)],
            name="feedback_signal_created_at",
        )

    def create(self, document: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_feedback_event_document(document)
        result = self.collection.insert_one(normalized)
        normalized["_id"] = result.inserted_id
        return normalized

    def delete_reactions_for_target(self, *, target_type: str, target_id: str) -> int:
        liked_result = self.collection.delete_many(
            {"target_type": target_type, "target_id": target_id, "signal": "liked"}
        )
        disliked_result = self.collection.delete_many(
            {"target_type": target_type, "target_id": target_id, "signal": "disliked"}
        )
        return int(liked_result.deleted_count) + int(disliked_result.deleted_count)

    def clear_notes_for_target(self, *, target_type: str, target_id: str) -> int:
        deleted_notes = self.collection.delete_many(
            {"target_type": target_type, "target_id": target_id, "signal": "note"}
        )
        liked_updated = self.collection.update_many(
            {"target_type": target_type, "target_id": target_id, "signal": "liked"},
            {"$set": {"notes": ""}},
        )
        disliked_updated = self.collection.update_many(
            {"target_type": target_type, "target_id": target_id, "signal": "disliked"},
            {"$set": {"notes": ""}},
        )
        return (
            int(deleted_notes.deleted_count)
            + int(liked_updated.modified_count)
            + int(disliked_updated.modified_count)
        )

    def list_for_target(
        self, *, target_type: str, target_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        cursor = (
            self.collection.find({"target_type": target_type, "target_id": target_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return list(cursor)

    def list_for_targets(
        self, *, target_type: str, target_ids: list[str]
    ) -> list[dict[str, Any]]:
        if not target_ids:
            return []
        cursor = self.collection.find(
            {"target_type": target_type, "target_id": {"$in": target_ids}}
        ).sort("created_at", DESCENDING)
        return list(cursor)

    def list_recent(self, *, limit: int = 300) -> list[dict[str, Any]]:
        return list(
            self.collection.find({}).sort("created_at", DESCENDING).limit(limit)
        )

    def latest_for_target(
        self, *, target_type: str, target_id: str
    ) -> dict[str, Any] | None:
        events = self.list_for_target(
            target_type=target_type, target_id=target_id, limit=1
        )
        return events[0] if events else None
