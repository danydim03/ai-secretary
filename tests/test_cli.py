from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from secretary.cli import main


class LocalCliWorkflowTests(unittest.TestCase):
    def run_cli(self, arguments: list[str]) -> str:
        output = io.StringIO()
        with patch("sys.argv", ["secretary", *arguments]), contextlib.redirect_stdout(output):
            main()
        return output.getvalue()

    def test_ingest_retrieve_verify_and_audit_work_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = root / "store"
            source = root / "note.txt"
            source.write_text("La riunione si terrà il 12 maggio 2026.", encoding="utf-8")

            ingested = json.loads(self.run_cli(["--store", str(store), "ingest", str(source)]))
            self.assertFalse(ingested["duplicate"])
            show_path = root / "runs" / "shown.json"
            self.run_cli(["--store", str(store), "show-to-file", ingested["document_id"], str(show_path)])
            shown = json.loads(show_path.read_text(encoding="utf-8"))
            self.assertEqual(shown["source_filename"], "note.txt")
            self.assertIn("12 maggio 2026", shown["results"][0]["text"])
            packet_path = root / "runs" / "evidence.json"
            self.run_cli(["--store", str(store), "search-to-file", "riunione maggio", str(packet_path)])
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            evidence_id = packet["results"][0]["evidence_id"]
            claim_path = root / "runs" / "claims.json"
            claim_path.write_text(json.dumps({"claims": [{
                "claim_id": "c1",
                "text": "La riunione è il 12 maggio 2026.",
                "kind": "quoted",
                "status": "supported",
                "evidence": [evidence_id],
            }]}), encoding="utf-8")

            checked = json.loads(self.run_cli([
                "--store", str(store), "verify-claims", str(claim_path), "--evidence", str(packet_path),
            ]))
            self.assertTrue(checked["valid"])
            self.assertEqual(checked["citation_coverage"], 1.0)
            audit = json.loads(self.run_cli(["--store", str(store), "audit", "--limit", "50"]))
            self.assertEqual([event["event_type"] for event in audit["events"]], [
                "document_ingested", "document_shown", "evidence_searched", "claims_verified",
            ])


if __name__ == "__main__":
    unittest.main()
