from __future__ import annotations

from flask import Blueprint, render_template


web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def index() -> str:
    return render_template("index.html")
