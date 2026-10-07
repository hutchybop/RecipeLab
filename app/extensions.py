from __future__ import annotations

from typing import Tuple

from flask import Flask, current_app
from pymongo import MongoClient
from pymongo.database import Database


def init_extensions(app: Flask) -> None:
    mongo_client = MongoClient(
        app.config["MONGO_URI"],
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
    )
    app.extensions["mongo_client"] = mongo_client
    app.extensions["mongo_db"] = mongo_client[app.config["MONGO_DB_NAME"]]


def get_mongo_client() -> MongoClient:
    return current_app.extensions["mongo_client"]


def get_mongo_db() -> Database:
    return current_app.extensions["mongo_db"]


def mongo_health() -> Tuple[bool, str | None]:
    try:
        get_mongo_client().admin.command("ping")
        return True, None
    except Exception as exc:  # pragma: no cover
        return False, str(exc)
