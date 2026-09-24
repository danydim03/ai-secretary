from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .ingest import verify_source_integrity
from .validation import validate_document


_CLAIM_KINDS = {"quoted", "derived", "inferred", "assumption"}
_STATUSES = {"supported", "unsupported", "assumption"}
_EVIDENCE_ID = re.compile(r"^ev_(doc_[a-f0-9]+)_(blk_[A-Za-z0-9_]+)$")


def _evidence_index(store: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    canonical_dir = store / "canonical"
    for path in sorted(canonical_dir.glob("doc_*.json")) if canonical_dir.is_dir() else []:
        document = json.loads(path.read_text(encoding="utf-8"))
        validate_document(document)
        verify_source_integrity(document, store)
        for block in document["blocks"]:
            evidence_id = f"ev_{document['document_id']}_{block['block_id']}"
            index[evidence_id] = {
                "document_id": document["document_id"],
                "block_id": block["block_id"],
                "text": block["normalized_text"],
                "source_locator": block["source_locator"],
                "source_filename": document["source"]["original_filename"],
                "source_sha256": document["source"]["sha256"],
            }
    return index


def validate_claim_set(
    claim_set: Any,
    store: Path,
    allowed_evidence_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Check claim structure and evidence links against the local canonical store.

    This deterministic MVP checks citation existence and non-empty evidence; it
    deliberately does not claim semantic entailment between a passage and claim.
    """
    if not isinstance(claim_set, dict) or not isinstance(claim_set.get("claims"), list):
        raise ValueError("Il claim set deve essere un oggetto JSON con un array 'claims'.")
    unexpected_set_fields = set(claim_set) - {"claims"}

    known_evidence = _evidence_index(store)
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    if unexpected_set_fields:
        errors.append({"claim_id": "claim_set", "error": f"proprietà non ammesse: {', '.join(sorted(unexpected_set_fields))}"})

    for position, claim in enumerate(claim_set["claims"], 1):
        location = f"claims[{position - 1}]"
        if not isinstance(claim, dict):
            errors.append({"claim_id": f"claim_{position}", "error": f"{location}: deve essere un oggetto."})
            continue

        claim_id = claim.get("claim_id")
        text = claim.get("text")
        kind = claim.get("kind")
        status = claim.get("status")
        evidence = claim.get("evidence")
        claim_errors: list[str] = []
        unexpected_fields = set(claim) - {"claim_id", "text", "kind", "status", "evidence", "confidence"}
        if unexpected_fields:
            claim_errors.append(f"proprietà non ammesse: {', '.join(sorted(unexpected_fields))}")

        if not isinstance(claim_id, str) or not claim_id.strip():
            claim_errors.append("claim_id mancante o vuoto")
            claim_id = f"claim_{position}"
        elif claim_id in seen:
            claim_errors.append("claim_id duplicato")
        seen.add(claim_id)
        if not isinstance(text, str) or not text.strip():
            claim_errors.append("text mancante o vuoto")
        if kind not in _CLAIM_KINDS:
            claim_errors.append(f"kind deve essere uno fra {', '.join(sorted(_CLAIM_KINDS))}")
        if status not in _STATUSES:
            claim_errors.append(f"status deve essere uno fra {', '.join(sorted(_STATUSES))}")
        if (kind == "assumption") != (status == "assumption"):
            claim_errors.append("kind e status devono entrambi essere assumption per un'ipotesi")
        confidence = claim.get("confidence")
        if "confidence" in claim and confidence is not None and (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
        ):
            claim_errors.append("confidence deve essere un numero finito fra 0 e 1 oppure null")
        if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
            claim_errors.append("evidence deve essere un array di evidence_id")
            evidence = []

        linked: list[str] = []
        for evidence_id in evidence:
            if not _EVIDENCE_ID.fullmatch(evidence_id):
                claim_errors.append(f"formato evidence_id non valido: {evidence_id}")
            elif evidence_id not in known_evidence:
                claim_errors.append(f"evidence_id inesistente: {evidence_id}")
            elif allowed_evidence_ids is not None and evidence_id not in allowed_evidence_ids:
                claim_errors.append(f"evidence_id non incluso nel pacchetto recuperato: {evidence_id}")
            else:
                linked.append(evidence_id)

        is_assumption = kind == "assumption" or status == "assumption"
        if not linked and not is_assumption:
            claim_errors.append("un claim fattuale deve citare almeno un'evidenza esistente")
        if linked and status == "assumption":
            claim_errors.append("un claim con evidenze non può essere marcato assumption")

        row = {"claim_id": claim_id, "text": text, "kind": kind, "status": status, "evidence": linked}
        if claim_errors:
            errors.append({"claim_id": claim_id, "error": "; ".join(claim_errors)})
            row["status"] = "unsupported"
        else:
            row["evidence_details"] = [known_evidence[item] for item in linked]
        checked.append(row)

    factual = [item for item in checked if item.get("kind") != "assumption" and item.get("status") != "assumption"]
    supported = [item for item in factual if item.get("status") == "supported" and item.get("evidence")]
    return {
        "valid": not errors,
        "citation_coverage": round(len(supported) / len(factual), 4) if factual else 1.0,
        "claim_count": len(checked),
        "factual_claim_count": len(factual),
        "supported_factual_claim_count": len(supported),
        "claims": checked,
        "errors": errors,
    }


def load_claim_set(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON non valido alla riga {exc.lineno}, colonna {exc.colno}: {exc.msg}") from exc


def load_evidence_ids(path: Path) -> set[str]:
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Pacchetto evidenze JSON non valido alla riga {exc.lineno}, colonna {exc.colno}: {exc.msg}") from exc
    results = packet.get("results") if isinstance(packet, dict) else None
    if not isinstance(results, list):
        raise ValueError("Il pacchetto evidenze deve avere un array 'results'.")
    ids = {item.get("evidence_id") for item in results if isinstance(item, dict)}
    if any(not isinstance(item, str) for item in ids):
        raise ValueError("Tutte le evidenze devono avere un evidence_id testuale.")
    return ids  # type: ignore[return-value]
