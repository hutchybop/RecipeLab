from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass
class FakeInsertResult:
    inserted_id: Any


@dataclass
class FakeUpdateResult:
    modified_count: int


@dataclass
class FakeDeleteResult:
    deleted_count: int


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self._docs = docs
        self._limit = None

    def sort(self, key: str, direction: int) -> "FakeCursor":
        reverse = direction == -1
        self._docs.sort(key=lambda item: item.get(key), reverse=reverse)
        return self

    def limit(self, value: int) -> "FakeCursor":
        self._limit = value
        return self

    def __iter__(self):
        if self._limit is None:
            return iter(self._docs)
        return iter(self._docs[: self._limit])


class FakeCollection:
    def __init__(self):
        self.docs: list[dict[str, Any]] = []
        self.indexes: list[dict[str, Any]] = []
        self._next_id = 1

    def create_index(self, keys, **kwargs):
        self.indexes.append({"keys": keys, **kwargs})
        return kwargs.get("name", "index")

    def insert_one(self, document: dict[str, Any]) -> FakeInsertResult:
        to_store = deepcopy(document)
        to_store.setdefault("_id", self._next_id)
        self._next_id += 1
        self.docs.append(to_store)
        return FakeInsertResult(inserted_id=to_store["_id"])

    def find_one(self, filters: dict[str, Any]) -> dict[str, Any] | None:
        for doc in self.docs:
            if _matches(doc, filters):
                return deepcopy(doc)
        return None

    def find(self, filters: dict[str, Any]) -> FakeCursor:
        matched = [deepcopy(doc) for doc in self.docs if _matches(doc, filters)]
        return FakeCursor(matched)

    def update_one(
        self, filters: dict[str, Any], update: dict[str, Any], upsert: bool = False
    ) -> FakeUpdateResult:
        for index, doc in enumerate(self.docs):
            if _matches(doc, filters):
                self.docs[index] = _apply_update(doc, update)
                return FakeUpdateResult(modified_count=1)

        if upsert:
            new_doc = deepcopy(filters)
            new_doc = _apply_update(new_doc, update)
            if "_id" not in new_doc:
                new_doc["_id"] = self._next_id
                self._next_id += 1
            self.docs.append(new_doc)
            return FakeUpdateResult(modified_count=1)

        return FakeUpdateResult(modified_count=0)

    def update_many(
        self, filters: dict[str, Any], update: dict[str, Any]
    ) -> FakeUpdateResult:
        updated = 0
        for index, doc in enumerate(self.docs):
            if _matches(doc, filters):
                self.docs[index] = _apply_update(doc, update)
                updated += 1
        return FakeUpdateResult(modified_count=updated)

    def delete_many(self, filters: dict[str, Any]) -> FakeDeleteResult:
        before = len(self.docs)
        self.docs = [doc for doc in self.docs if not _matches(doc, filters)]
        return FakeDeleteResult(deleted_count=before - len(self.docs))


class FakeDatabase:
    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


def _matches(document: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if isinstance(value, dict) and "$in" in value:
            if document.get(key) not in value["$in"]:
                return False
            continue
        if document.get(key) != value:
            return False
    return True


def _apply_update(document: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(document)
    for field, value in update.get("$set", {}).items():
        output[field] = value
    for field, value in update.get("$setOnInsert", {}).items():
        output.setdefault(field, value)
    return output
