from __future__ import annotations

from typing import Any

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from ..services.schema_utils import utc_now


class RuntimeSettingsRepository:
    collection_name = "runtime_settings"
    _model_key = "generation_model"

    def __init__(self, db: Database):
        self.collection: Collection = db[self.collection_name]

    @classmethod
    def ensure_indexes(cls, db: Database) -> None:
        collection = db[cls.collection_name]
        collection.create_index([("key", ASCENDING)], unique=True, name="runtime_settings_key_unique")

    def get_selected_model(self) -> str:
        record = self.collection.find_one({"key": self._model_key})
        if not record:
            return ""
        return str(record.get("value", "")).strip()

    def set_selected_model(self, model: str) -> dict[str, Any]:
        now = utc_now()
        document = {
            "key": self._model_key,
            "value": str(model).strip(),
            "updated_at": now,
        }
        self.collection.update_one(
            {"key": self._model_key},
            {
                "$set": document,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        return self.collection.find_one({"key": self._model_key}) or document
