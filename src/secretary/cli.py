from __future__ import annotations

import argparse
import hashlib
import json
import sys
import os
from pathlib import Path

from .ingest import ingest, load_document
from .validation import validate_document
from .retrieval import search_documents
from .claims import load_claim_set, load_evidence_ids, validate_claim_set
from .audit import record_event


def main() -> None:
    os.environ.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1]))
    parser = argparse.ArgumentParser(prog="secretary", description="AI Secretary, archivio documentale locale")
    parser.add_argument("--store", type=Path, default=Path("data"), help="Cartella archivio (default: ./data)")
    sub = parser.add_subparsers(dest="command", required=True)
    p_ingest = sub.add_parser("ingest", help="Archivia e canonicalizza un PDF, TXT o DOCX")
    p_ingest.add_argument("file", type=Path)
    p_show = sub.add_parser("show", help="Mostra testo e avvisi di un documento")
    p_show.add_argument("document_id")
    p_show_file = sub.add_parser("show-to-file", help=argparse.SUPPRESS)
    p_show_file.add_argument("document_id")
    p_show_file.add_argument("output", type=Path)
    p_list = sub.add_parser("list", help="Elenca documenti archiviati")
    p_validate = sub.add_parser("validate", help="Valida lo schema di un documento archiviato")
    p_validate.add_argument("document_id")
    p_search = sub.add_parser("search", help="Cerca localmente e restituisce evidenze con provenienza")
    p_search.add_argument("query", help="Termini da cercare nei documenti canonici")
    p_search.add_argument("--limit", type=int, default=8, help="Numero massimo di evidenze (1-50)")
    p_search.add_argument("--document", action="append", dest="document_ids", help="Limita la ricerca a questo document_id; ripetibile")
    p_search_file = sub.add_parser("search-to-file", help=argparse.SUPPRESS)
    p_search_file.add_argument("query")
    p_search_file.add_argument("output", type=Path)
    p_search_file.add_argument("--limit", type=int, default=6)
    p_search_file.add_argument("--document", action="append", dest="document_ids")
    p_check = sub.add_parser("verify-claims", help="Verifica struttura e riferimenti di un claim set JSON")
    p_check.add_argument("file", type=Path, help="Percorso al claim set JSON")
    p_check.add_argument("--evidence", type=Path, help="Limita le citazioni a un pacchetto restituito da search-to-file")
    p_event = sub.add_parser("record-event", help=argparse.SUPPRESS)
    p_event.add_argument("event_type")
    p_event.add_argument("metadata", help="Oggetto JSON privo di testo sorgente o prompt")
    p_audit = sub.add_parser("audit", help="Mostra gli ultimi eventi locali senza contenuti documentali")
    p_audit.add_argument("--limit", type=int, default=50, help="Numero massimo di eventi (1-500)")
    args = parser.parse_args()
    try:
        if args.command == "ingest":
            result = ingest(args.file, args.store)
            doc = result["document"]
            record_event(args.store, "document_ingested", {
                "document_id": doc["document_id"],
                "source_id": doc["source"]["source_id"],
                "source_sha256": doc["source"]["sha256"],
                "block_count": len(doc["blocks"]),
                "warning_codes": [warning["code"] for warning in doc["extraction_warnings"]],
                "duplicate": result["duplicate"],
            })
            print(json.dumps({"document_id": doc["document_id"], "sha256": doc["source"]["sha256"], "blocks": len(doc["blocks"]), "warnings": doc["extraction_warnings"], "canonical_path": result["canonical_path"], "duplicate": result["duplicate"]}, ensure_ascii=False, indent=2))
        elif args.command == "show":
            doc = load_document(args.document_id, args.store)
            record_event(args.store, "document_shown", {"document_id": args.document_id, "block_count": len(doc["blocks"])})
            print(f"{doc['source']['original_filename']} ({doc['document_id']})")
            for block in doc["blocks"]:
                where = f"pagina {block['source_locator']['page']}: " if "page" in block["source_locator"] else ""
                print(f"[{block['block_id']}] {where}{block['raw_text']}")
            if doc["extraction_warnings"]:
                print("\nAVVISI")
                for warning in doc["extraction_warnings"]:
                    print(f"- {warning['message']}")
        elif args.command == "show-to-file":
            doc = load_document(args.document_id, args.store)
            record_event(args.store, "document_shown", {"document_id": args.document_id, "block_count": len(doc["blocks"])})
            packet = {
                "document_id": doc["document_id"],
                "source_id": doc["source"]["source_id"],
                "source_filename": doc["source"]["original_filename"],
                "source_sha256": doc["source"]["sha256"],
                "results": [{
                    "evidence_id": f"ev_{doc['document_id']}_{block['block_id']}",
                    "source_filename": doc["source"]["original_filename"],
                    "source_sha256": doc["source"]["sha256"],
                    "block_id": block["block_id"],
                    "type": block["type"],
                    "source_locator": block["source_locator"],
                    "text": block["raw_text"],
                } for block in doc["blocks"]],
                "extraction_warnings": doc["extraction_warnings"],
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"blocks": len(packet["results"]), "output": str(args.output)}, ensure_ascii=False))
        elif args.command == "validate":
            doc = load_document(args.document_id, args.store)
            validate_document(doc)
            record_event(args.store, "document_validated", {"document_id": args.document_id, "valid": True})
            print(f"OK: {args.document_id} rispetta il contratto CanonicalDocument")
        elif args.command == "search":
            result = search_documents(args.query, args.store, args.limit, args.document_ids)
            record_event(args.store, "evidence_searched", {
                "query_sha256": hashlib.sha256(args.query.encode("utf-8")).hexdigest(),
                "searched_blocks": result["searched_blocks"],
                "result_count": len(result["results"]),
                "evidence_ids": [item["evidence_id"] for item in result["results"]],
            })
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "search-to-file":
            result = search_documents(args.query, args.store, args.limit, args.document_ids)
            record_event(args.store, "evidence_searched", {
                "query_sha256": hashlib.sha256(args.query.encode("utf-8")).hexdigest(),
                "searched_blocks": result["searched_blocks"],
                "result_count": len(result["results"]),
                "evidence_ids": [item["evidence_id"] for item in result["results"]],
            })
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"results": len(result["results"]), "output": str(args.output)}, ensure_ascii=False))
        elif args.command == "verify-claims":
            allowed = load_evidence_ids(args.evidence) if args.evidence else None
            result = validate_claim_set(load_claim_set(args.file), args.store, allowed)
            record_event(args.store, "claims_verified", {
                "valid": result["valid"],
                "claim_count": result["claim_count"],
                "citation_coverage": result["citation_coverage"],
                "error_count": len(result["errors"]),
            })
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "record-event":
            metadata = json.loads(args.metadata)
            event = record_event(args.store, args.event_type, metadata)
            print(json.dumps({"event_id": event["event_id"], "event_type": event["event_type"]}, ensure_ascii=False))
        elif args.command == "audit":
            if isinstance(args.limit, bool) or not 1 <= args.limit <= 500:
                raise ValueError("Il limite audit deve essere compreso tra 1 e 500.")
            journal = args.store.expanduser().resolve() / "audit" / "events.jsonl"
            events = []
            if journal.is_file():
                lines = journal.read_text(encoding="utf-8").splitlines()
                events = [json.loads(line) for line in lines[-args.limit:]]
            print(json.dumps({"events": events, "journal": str(journal)}, ensure_ascii=False, indent=2))
        else:
            store = args.store.expanduser().resolve()
            paths = sorted((store / "canonical").glob("doc_*.json")) if (store / "canonical").exists() else []
            record_event(args.store, "document_listed", {"document_count": len(paths)})
            for path in paths:
                doc = json.loads(path.read_text(encoding="utf-8"))
                print(f"{doc['document_id']}\t{doc['source']['original_filename']}\t{len(doc['blocks'])} blocchi")
    except (OSError, ValueError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
