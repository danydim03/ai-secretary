from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def record_event(store: Path, event_type: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Append a small, content-free event to the local JSONL audit journal."""
    if not isinstance(event_type, str) or not event_type.strip() or len(event_type) > 80:
        raise ValueError("event_type deve essere una stringa non vuota di massimo 80 caratteri.")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata deve essere un oggetto JSON.")

    event = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "at": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "metadata": metadata or {},
    }
    audit_dir = store.expanduser().resolve() / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    journal = audit_dir / "events.jsonl"
    encoded = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(journal, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        written = os.write(descriptor, encoded)
        if written != len(encoded):
            raise OSError("Scrittura incompleta del journal audit.")
    finally:
        os.close(descriptor)
    return event
