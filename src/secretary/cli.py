from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path

from .ingest import ingest, load_document
from .validation import validate_document
from .retrieval import search_documents


def main() -> None:
    os.environ.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1]))
    parser = argparse.ArgumentParser(prog="secretary", description="AI Secretary, archivio documentale locale")
    parser.add_argument("--store", type=Path, default=Path("data"), help="Cartella archivio (default: ./data)")
    sub = parser.add_subparsers(dest="command", required=True)
    p_ingest = sub.add_parser("ingest", help="Archivia e canonicalizza un PDF, TXT o DOCX")
    p_ingest.add_argument("file", type=Path)
    p_show = sub.add_parser("show", help="Mostra testo e avvisi di un documento")
    p_show.add_argument("document_id")
    p_list = sub.add_parser("list", help="Elenca documenti archiviati")
    p_validate = sub.add_parser("validate", help="Valida lo schema di un documento archiviato")
    p_validate.add_argument("document_id")
    p_search = sub.add_parser("search", help="Cerca localmente e restituisce evidenze con provenienza")
    p_search.add_argument("query", help="Termini da cercare nei documenti canonici")
    p_search.add_argument("--limit", type=int, default=8, help="Numero massimo di evidenze (1-50)")
    p_search.add_argument("--document", action="append", dest="document_ids", help="Limita la ricerca a questo document_id; ripetibile")
    args = parser.parse_args()
    try:
        if args.command == "ingest":
            result = ingest(args.file, args.store)
            doc = result["document"]
            print(json.dumps({"document_id": doc["document_id"], "sha256": doc["source"]["sha256"], "blocks": len(doc["blocks"]), "warnings": doc["extraction_warnings"], "canonical_path": result["canonical_path"]}, ensure_ascii=False, indent=2))
        elif args.command == "show":
            doc = load_document(args.document_id, args.store)
            print(f"{doc['source']['original_filename']} ({doc['document_id']})")
            for block in doc["blocks"]:
                where = f"pagina {block['source_locator']['page']}: " if "page" in block["source_locator"] else ""
                print(f"[{block['block_id']}] {where}{block['raw_text']}")
            if doc["extraction_warnings"]:
                print("\nAVVISI")
                for warning in doc["extraction_warnings"]:
                    print(f"- {warning['message']}")
        elif args.command == "validate":
            doc = load_document(args.document_id, args.store)
            validate_document(doc)
            print(f"OK: {args.document_id} rispetta il contratto CanonicalDocument")
        elif args.command == "search":
            result = search_documents(args.query, args.store, args.limit, args.document_ids)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            paths = sorted((args.store / "canonical").glob("doc_*.json")) if (args.store / "canonical").exists() else []
            for path in paths:
                doc = json.loads(path.read_text(encoding="utf-8"))
                print(f"{doc['document_id']}\t{doc['source']['original_filename']}\t{len(doc['blocks'])} blocchi")
    except (OSError, ValueError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
