from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from secretary.audit import record_event


class AuditJournalTests(unittest.TestCase):
    def test_appends_content_free_event_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = Path(temporary) / "data"
            first = record_event(store, "evidence_searched", {"query_sha256": "a" * 64, "result_count": 2})
            second = record_event(store, "claims_verified", {"valid": True, "citation_coverage": 1.0})
            events = [json.loads(line) for line in (store / "audit" / "events.jsonl").read_text(encoding="utf-8").splitlines()]

        self.assertEqual([event["event_id"] for event in events], [first["event_id"], second["event_id"]])
        self.assertEqual([event["event_type"] for event in events], ["evidence_searched", "claims_verified"])
        self.assertNotIn("query", events[0]["metadata"])


if __name__ == "__main__":
    unittest.main()
