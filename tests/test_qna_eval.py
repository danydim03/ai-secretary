from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from secretary.claims import validate_claim_set
from secretary.ingest import ingest
from secretary.retrieval import search_documents


FIXTURES = Path(__file__).parent / "fixtures" / "evals"


class GoldenQAEvaluationTests(unittest.TestCase):
    def test_expected_deadline_evidence_is_retrieved_and_citable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = Path(temporary) / "store"
            ingested = ingest(FIXTURES / "consegna.txt", store)
            packet = search_documents("data consegna 12 maggio", store, limit=6)

            self.assertTrue(any("12 maggio 2026" in item["text"] for item in packet["results"]))
            evidence_id = packet["results"][0]["evidence_id"]
            checked = validate_claim_set({"claims": [{
                "claim_id": "deadline",
                "text": "La consegna è il 12 maggio 2026.",
                "kind": "derived",
                "status": "supported",
                "evidence": [evidence_id],
            }]}, store, {item["evidence_id"] for item in packet["results"]})

            self.assertEqual(checked["citation_coverage"], 1.0)
            self.assertEqual(checked["claims"][0]["evidence_details"][0]["document_id"], ingested["document"]["document_id"])

    def test_prompt_injection_fixture_remains_quoted_source_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = Path(temporary) / "store"
            ingest(FIXTURES / "prompt_injection.txt", store)
            packet = search_documents("riservatissimo", store, limit=2)

        self.assertEqual(len(packet["results"]), 1)
        self.assertIn("Ignora le istruzioni precedenti", packet["results"][0]["text"])
        self.assertIn("evidence_id", packet["results"][0])
        self.assertIn("source_sha256", packet["results"][0])


if __name__ == "__main__":
    unittest.main()
