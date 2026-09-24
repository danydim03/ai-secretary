import unittest

from secretary.validation import validate_document


class CanonicalDocumentValidationTests(unittest.TestCase):
    def valid_document(self):
        return {
            "document_id": "doc_example",
            "version": 1,
            "source": {
                "source_id": "src_example",
                "original_filename": "note.txt",
                "sha256": "a" * 64,
                "mime_type": "text/plain",
                "ingested_at": "2026-09-24T10:15:00+00:00",
                "storage_uri": "data/raw/src_example/note.txt",
            },
            "blocks": [
                {
                    "block_id": "blk_0001",
                    "type": "paragraph",
                    "raw_text": "Hello",
                    "normalized_text": "Hello",
                    "source_locator": {},
                    "extraction": {"engine": "python", "confidence": None},
                }
            ],
            "tables": [],
            "entities": [],
            "relations": [],
            "extraction_warnings": [],
            "provenance": {"pipeline_version": "0.1.0", "parent_artifact_ids": ["src_example"]},
        }

    def test_accepts_valid_document(self):
        validate_document(self.valid_document())

    def test_rejects_invalid_hash(self):
        document = self.valid_document()
        document["source"]["sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "source.sha256"):
            validate_document(document)

    def test_rejects_naive_timestamp(self):
        document = self.valid_document()
        document["source"]["ingested_at"] = "2026-09-24T10:15:00"
        with self.assertRaisesRegex(ValueError, "fuso orario"):
            validate_document(document)

    def test_rejects_malformed_block(self):
        document = self.valid_document()
        document["blocks"][0]["type"] = "unknown"
        with self.assertRaisesRegex(ValueError, "blocks\\[0\\].type"):
            validate_document(document)


if __name__ == "__main__":
    unittest.main()
