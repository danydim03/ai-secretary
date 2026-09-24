from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from secretary.claims import validate_claim_set
from secretary.ingest import ingest


class ClaimVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.store = self.root / "store"
        source = self.root / "source.txt"
        source.write_text("La data di consegna è il 12 maggio 2026.\n", encoding="utf-8")
        self.document = ingest(source, self.store)["document"]
        self.evidence_id = f"ev_{self.document['document_id']}_{self.document['blocks'][0]['block_id']}"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_accepts_existing_evidence_and_resolves_provenance(self) -> None:
        result = validate_claim_set({"claims": [{
            "claim_id": "c1",
            "text": "La consegna è il 12 maggio 2026.",
            "kind": "quoted",
            "status": "supported",
            "evidence": [self.evidence_id],
        }]}, self.store)

        self.assertTrue(result["valid"])
        self.assertEqual(result["citation_coverage"], 1.0)
        self.assertEqual(result["claims"][0]["evidence_details"][0]["source_filename"], "source.txt")

    def test_rejects_unknown_evidence_for_factual_claim(self) -> None:
        result = validate_claim_set({"claims": [{
            "claim_id": "c1",
            "text": "Un fatto non provato.",
            "kind": "derived",
            "status": "supported",
            "evidence": ["ev_doc_abcdef_blk_missing"],
        }]}, self.store)

        self.assertFalse(result["valid"])
        self.assertEqual(result["citation_coverage"], 0.0)
        self.assertIn("inesistente", result["errors"][0]["error"])

    def test_rejects_valid_but_unretrieved_evidence(self) -> None:
        result = validate_claim_set({"claims": [{
            "claim_id": "c1",
            "text": "Un fatto con una citazione estranea al retrieval.",
            "kind": "derived",
            "status": "supported",
            "evidence": [self.evidence_id],
        }]}, self.store, allowed_evidence_ids={"ev_doc_abcdef_blk_other"})

        self.assertFalse(result["valid"])
        self.assertEqual(result["citation_coverage"], 0.0)
        self.assertIn("non incluso nel pacchetto", result["errors"][0]["error"])

    def test_allows_explicit_assumption_without_evidence(self) -> None:
        result = validate_claim_set({"claims": [{
            "claim_id": "c1",
            "text": "Potrebbe essere una consegna interna.",
            "kind": "assumption",
            "status": "assumption",
            "evidence": [],
        }]}, self.store)

        self.assertTrue(result["valid"])
        self.assertEqual(result["citation_coverage"], 1.0)

    def test_rejects_inconsistent_assumption_and_invalid_confidence(self) -> None:
        result = validate_claim_set({"claims": [{
            "claim_id": "c1",
            "text": "Una formulazione ambigua.",
            "kind": "derived",
            "status": "assumption",
            "evidence": [],
            "confidence": 2.0,
        }]}, self.store)

        self.assertFalse(result["valid"])
        self.assertIn("devono entrambi essere assumption", result["errors"][0]["error"])
        self.assertIn("confidence", result["errors"][0]["error"])


if __name__ == "__main__":
    unittest.main()
