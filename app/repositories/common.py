from __future__ import annotations

from typing import Any

from bson import ObjectId


def to_object_id(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    return value
