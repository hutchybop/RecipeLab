from __future__ import annotations

from flask import Blueprint, jsonify

from ...extensions import mongo_health


api_bp = Blueprint("api", __name__)


@api_bp.get("/health")
def health_check():
    mongo_ok, error_message = mongo_health()
    payload = {
        "status": "ok" if mongo_ok else "degraded",
        "services": {
            "api": "ok",
            "mongo": "ok" if mongo_ok else "error",
        },
    }
    if error_message:
        payload["services"]["mongo_error"] = error_message
    status_code = 200 if mongo_ok else 503
    return jsonify(payload), status_code
