from __future__ import annotations

import re
import math
from datetime import datetime
from typing import Any


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_block(block: Any, location: str, errors: list[str]) -> None:
    if not isinstance(block, dict):
        errors.append(f"{location}: atteso un oggetto")
        return

    required = ("block_id", "type", "raw_text", "normalized_text", "source_locator", "extraction")
    for key in required:
        if key not in block:
            errors.append(f"{location}.{key}: campo obbligatorio mancante")

    if not isinstance(block.get("block_id"), str) or not block["block_id"].startswith("blk_"):
        errors.append(f"{location}.block_id: deve essere una stringa che inizia con 'blk_'")
    block_type = block.get("type")
    if not isinstance(block_type, str) or block_type not in {"paragraph", "heading", "table"}:
        errors.append(f"{location}.type: valore non ammesso")
    for key in ("raw_text", "normalized_text"):
        if key in block and not isinstance(block[key], str):
            errors.append(f"{location}.{key}: attesa una stringa")

    locator = block.get("source_locator")
    if not isinstance(locator, dict):
        errors.append(f"{location}.source_locator: atteso un oggetto")
    else:
        for key in ("page", "paragraph_index", "table_index", "body_index"):
            if key in locator and (not _is_int(locator[key]) or locator[key] < 1):
                errors.append(f"{location}.source_locator.{key}: atteso un intero positivo")
        bbox = locator.get("bbox")
        if bbox is not None and (
            not isinstance(bbox, list)
            or len(bbox) != 4
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in bbox)
        ):
            errors.append(f"{location}.source_locator.bbox: attesi quattro numeri finiti [x0, y0, x1, y1]")
        char_range = locator.get("char_range")
        if char_range is not None and (
            not isinstance(char_range, list)
            or len(char_range) != 2
            or any(not _is_int(value) or value < 0 for value in char_range)
            or (isinstance(char_range, list) and len(char_range) == 2 and all(_is_int(value) for value in char_range) and char_range[1] < char_range[0])
        ):
            errors.append(f"{location}.source_locator.char_range: attesi due offset interi non negativi in ordine")

    extraction = block.get("extraction")
    if not isinstance(extraction, dict):
        errors.append(f"{location}.extraction: atteso un oggetto")
    else:
        if not isinstance(extraction.get("engine"), str):
            errors.append(f"{location}.extraction.engine: attesa una stringa")
        confidence = extraction.get("confidence")
        if confidence is not None and (isinstance(confidence, bool) or not isinstance(confidence, (int, float))):
            errors.append(f"{location}.extraction.confidence: atteso un numero o null")


def validate_document(document: Any) -> None:
    """Validate the CanonicalDocument contract without third-party packages.

    The checks mirror the fields and constraints currently defined in
    schemas/canonical_document.schema.json. Raises ValueError with all detected
    issues so callers can show actionable feedback.
    """
    errors: list[str] = []
    if not isinstance(document, dict):
        raise ValueError("Canonical Document non valido: atteso un oggetto JSON")

    required = (
        "document_id", "version", "source", "blocks", "tables", "entities",
        "relations", "extraction_warnings", "provenance",
    )
    for key in required:
        if key not in document:
            errors.append(f"{key}: campo obbligatorio mancante")

    document_id = document.get("document_id")
    if not isinstance(document_id, str) or not document_id.startswith("doc_"):
        errors.append("document_id: deve essere una stringa che inizia con 'doc_'")
    version = document.get("version")
    if not _is_int(version) or version < 1:
        errors.append("version: atteso un intero maggiore o uguale a 1")

    source = document.get("source")
    source_fields = ("source_id", "original_filename", "sha256", "mime_type", "ingested_at", "storage_uri")
    if not isinstance(source, dict):
        errors.append("source: atteso un oggetto")
    else:
        for key in source_fields:
            if key not in source:
                errors.append(f"source.{key}: campo obbligatorio mancante")
        for key in source.keys() - set(source_fields):
            errors.append(f"source.{key}: proprietà non ammessa dallo schema")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id.startswith("src_"):
            errors.append("source.source_id: deve essere una stringa che inizia con 'src_'")
        for key in ("original_filename", "mime_type", "ingested_at", "storage_uri"):
            if key in source and not isinstance(source[key], str):
                errors.append(f"source.{key}: attesa una stringa")
        digest = source.get("sha256")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            errors.append("source.sha256: atteso un hash SHA-256 esadecimale di 64 caratteri minuscoli")
        timestamp = source.get("ingested_at")
        if isinstance(timestamp, str):
            try:
                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    errors.append("source.ingested_at: il timestamp deve includere il fuso orario")
            except ValueError:
                errors.append("source.ingested_at: data/ora ISO 8601 non valida")

    for field in ("blocks", "tables", "entities", "relations", "extraction_warnings"):
        if field in document and not isinstance(document[field], list):
            errors.append(f"{field}: atteso un array")

    for field in ("blocks", "tables"):
        items = document.get(field)
        if isinstance(items, list):
            for index, block in enumerate(items):
                _check_block(block, f"{field}[{index}]", errors)

    warnings = document.get("extraction_warnings")
    if isinstance(warnings, list):
        for index, warning in enumerate(warnings):
            location = f"extraction_warnings[{index}]"
            if not isinstance(warning, dict):
                errors.append(f"{location}: atteso un oggetto")
                continue
            for key in ("code", "message"):
                if not isinstance(warning.get(key), str):
                    errors.append(f"{location}.{key}: attesa una stringa")
            if "page" in warning and not _is_int(warning["page"]):
                errors.append(f"{location}.page: atteso un intero")

    provenance = document.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance: atteso un oggetto")
    else:
        if not isinstance(provenance.get("pipeline_version"), str):
            errors.append("provenance.pipeline_version: attesa una stringa")
        parents = provenance.get("parent_artifact_ids")
        if not isinstance(parents, list) or any(not isinstance(item, str) for item in parents):
            errors.append("provenance.parent_artifact_ids: atteso un array di stringhe")

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Canonical Document non valido:\n{details}")
