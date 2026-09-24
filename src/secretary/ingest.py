from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .validation import validate_document


SUPPORTED = {".pdf", ".txt", ".docx"}


def _block(
    page: int | None,
    index: int,
    text: str,
    kind: str = "paragraph",
    locator: dict[str, Any] | None = None,
    engine: str | None = None,
    normalized_text: str | None = None,
) -> dict[str, Any]:
    source_locator = dict(locator or {})
    if page is not None:
        source_locator["page"] = page
    return {
        "block_id": f"blk_{page:04d}_{index:04d}" if page is not None else f"blk_{index:04d}",
        "type": kind,
        "raw_text": text,
        "normalized_text": text if normalized_text is None else normalized_text,
        "source_locator": source_locator,
        "extraction": {"engine": engine or ("pymupdf" if page is not None else "python-docx/python"), "confidence": None},
    }


def extract(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ext = path.suffix.lower()
    blocks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if ext == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise ValueError("Per leggere PDF installa le dipendenze con: python -m pip install -e .") from exc
        with fitz.open(path) as pdf:
            for page_no, page in enumerate(pdf, 1):
                text_blocks = [item for item in page.get_text("blocks") if len(item) < 7 or item[6] == 0]
                char_offset = 0
                page_block_index = 0
                for item in text_blocks:
                    x0, y0, x1, y1, text = item[:5]
                    if not text.strip():
                        continue
                    page_block_index += 1
                    char_end = char_offset + len(text)
                    locator = {
                        "bbox": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                        "char_range": [char_offset, char_end],
                    }
                    blocks.append(_block(page_no, page_block_index, text, locator=locator, normalized_text=text.strip()))
                    char_offset = char_end
                if page_block_index == 0:
                    warnings.append({"code": "page_without_text", "page": page_no, "message": "Nessun testo digitale rilevato; possibile scansione da sottoporre a OCR."})
                if page.get_images(full=True):
                    warnings.append({"code": "page_contains_images", "page": page_no, "message": "La pagina contiene immagini non sottoposte a OCR; il testo al loro interno potrebbe non essere estratto."})
    elif ext == ".txt":
        raw_bytes = path.read_bytes()
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            text = raw_bytes.decode("utf-8", errors="replace")
            warnings.append({
                "code": "text_decode_replacement",
                "message": f"Codifica UTF-8 non valida ai byte {exc.start}-{exc.end}; i caratteri non decodificabili sono rappresentati con U+FFFD. L'originale binario è conservato.",
            })
        if text:
            normalized = text.replace("\r\n", "\n").replace("\r", "\n")
            blocks.append(_block(None, 1, text, locator={"char_range": [0, len(text)]}, engine="python:utf-8", normalized_text=normalized))
        else:
            warnings.append({"code": "empty_text_file", "message": "Il file TXT è vuoto; non sono stati creati blocchi di testo."})
    elif ext == ".docx":
        try:
            from docx import Document as DocxDocument
            from docx.table import Table
            from docx.text.paragraph import Paragraph
        except ImportError as exc:
            raise ValueError("Per leggere DOCX installa le dipendenze con: python -m pip install -e .") from exc
        doc = DocxDocument(path)
        table_no = 0
        paragraph_no = 0
        for i, item in enumerate(doc.iter_inner_content(), 1):
            if isinstance(item, Paragraph):
                paragraph_no += 1
                value = item.text
                style_name = item.style.name if item.style else ""
                locator = {"paragraph_index": paragraph_no, "body_index": i}
                blocks.append(_block(None, i, value, "heading" if style_name.startswith("Heading") else "paragraph", locator=locator, normalized_text=value.strip()))
            elif isinstance(item, Table):
                table_no += 1
                table = item
                locator = {"table_index": table_no, "body_index": i}
                rows = [[cell.text for cell in row.cells] for row in table.rows]
                table_text = json.dumps(rows, ensure_ascii=False)
                blocks.append({**_block(None, i, table_text, "table", locator=locator, normalized_text=table_text), "table_id": f"tbl_{table_no:04d}", "rows": rows})
        warnings.append({"code": "docx_non_body_content_not_extracted", "message": "L'estrazione copre paragrafi e tabelle nel corpo del documento; immagini, intestazioni, piè di pagina, note e commenti non sono inclusi nel Canonical Document."})
    return blocks, warnings


def ingest(source: Path, store: Path) -> dict[str, Any]:
    source = source.expanduser().resolve()
    store = store.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"File non trovato: {source}")
    if source.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Formato non supportato: {source.suffix}. Formati disponibili: PDF, TXT, DOCX.")
    digest = _sha256_file(source)
    canonical_dir = store / "canonical"
    if canonical_dir.is_dir():
        for existing_path in sorted(canonical_dir.glob("doc_*.json")):
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            if existing.get("source", {}).get("sha256") == digest:
                validate_document(existing)
                verify_source_integrity(existing, store)
                return {"document": existing, "canonical_path": str(existing_path), "duplicate": True}
    source_id = f"src_{uuid.uuid4().hex}"
    document_id = f"doc_{uuid.uuid4().hex}"
    raw_dir = store / "raw" / source_id
    raw_dir.mkdir(parents=True, exist_ok=False)
    canonical_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / source.name
    shutil.copy2(source, raw_path)
    copied_digest = _sha256_file(raw_path)
    if copied_digest != digest:
        raise ValueError("La copia archiviata non corrisponde alla fonte originale; ingestione interrotta.")
    blocks, warnings = extract(raw_path)
    doc: dict[str, Any] = {
        "document_id": document_id,
        "version": 1,
        "source": {
            "source_id": source_id,
            "original_filename": source.name,
            "sha256": digest,
            "mime_type": mimetypes.guess_type(source.name)[0] or "application/octet-stream",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "storage_uri": str(raw_path),
        },
        "blocks": blocks,
        "tables": [b for b in blocks if b["type"] == "table"],
        "entities": [],
        "relations": [],
        "extraction_warnings": warnings,
        "provenance": {"pipeline_version": __version__, "parent_artifact_ids": [source_id]},
    }
    validate_document(doc)
    out = canonical_dir / f"{document_id}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"document": doc, "canonical_path": str(out), "duplicate": False}


def load_document(document_id: str, store: Path) -> dict[str, Any]:
    path = store / "canonical" / f"{document_id}.json"
    if not path.is_file():
        raise ValueError(f"Documento non trovato: {document_id}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    validate_document(doc)
    verify_source_integrity(doc, store)
    return doc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source_integrity(document: dict[str, Any], store: Path) -> None:
    """Ensure the archived original remains inside this store and matches its recorded hash."""
    source = document["source"]
    archived_path = Path(source["storage_uri"]).expanduser().resolve()
    raw_root = (store / "raw").expanduser().resolve()
    try:
        archived_path.relative_to(raw_root)
    except ValueError as exc:
        raise ValueError(f"La fonte archiviata esce dalla cartella raw: {source['source_id']}") from exc
    if not archived_path.is_file():
        raise ValueError(f"File originale mancante nell'archivio: {source['source_id']}")
    actual_hash = _sha256_file(archived_path)
    if actual_hash != source["sha256"]:
        raise ValueError(f"Integrità fonte non valida per {source['source_id']}: hash SHA-256 diverso.")
