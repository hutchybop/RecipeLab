from __future__ import annotations

import re
from typing import Any


def render_recipe_pdf(recipe: dict[str, Any]) -> bytes:
    title = str(recipe.get("title", "Untitled recipe"))
    metadata = recipe.get("metadata", {}) if isinstance(recipe, dict) else {}

    lines: list[str] = [
        f"Recipe: {title}",
        f"Meal Type: {recipe.get('meal_type', '')}",
        f"Source Type: {recipe.get('source_type', '')}",
        f"Servings: {metadata.get('servings', '')}",
        f"Prep/Cook: {metadata.get('prep_time', '')} / {metadata.get('cook_time', '')}",
        f"Difficulty: {metadata.get('difficulty', '')}",
        f"Rating: {metadata.get('rating', '')}",
        f"Tags: {', '.join(metadata.get('tags', [])) if isinstance(metadata.get('tags'), list) else ''}",
        "",
        "Ingredients:",
    ]

    for item in recipe.get("ingredients", []):
        if isinstance(item, dict):
            lines.append(f"- {item.get('quantity', '')} {item.get('unit', '')} {item.get('ingredient', '')}".strip())

    lines.append("")
    lines.append("Method:")
    for idx, step in enumerate(recipe.get("method", []), start=1):
        lines.append(f"{idx}. {step}")

    notes = recipe.get("notes", [])
    if notes:
        lines.append("")
        lines.append("Notes:")
        for note in notes:
            lines.append(f"- {note}")

    return _build_simple_pdf(lines)


def pdf_filename_for_recipe(recipe: dict[str, Any]) -> str:
    title = str(recipe.get("title", "recipe")).strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", title).strip("-") or "recipe"
    return f"{slug}.pdf"


def _build_simple_pdf(lines: list[str]) -> bytes:
    # Keep a safe top margin so first lines are not clipped by viewer/font ascent.
    content_lines = ["BT", "/F1 11 Tf", "50 742 Td", "14 TL"]
    for raw_line in lines:
        for part in _wrap_line(str(raw_line), max_chars=95):
            text = _escape_pdf_text(part)
            content_lines.append(f"({text}) Tj")
            content_lines.append("T*")
    content_lines.append("ET")

    stream_data = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        f"5 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("ascii") + stream_data + b"\nendstream\nendobj\n",
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)

    xref_start = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_line(value: str, *, max_chars: int) -> list[str]:
    text = value.strip()
    if not text:
        return [""]

    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]
