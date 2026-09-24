from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .ingest import verify_source_integrity
from .validation import validate_document


_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_K1 = 1.5
_B = 0.75
_MAX_EXCERPT_CHARS = 2_400
_MIN_CHAR_DICE = 0.5


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN_RE.findall(text)]


def _char_ngrams(token: str) -> set[str]:
    if len(token) < 4:
        return set()
    return {token[index:index + 3] for index in range(len(token) - 2)}


def _char_similarity(query_terms: list[str], document_tokens: list[str]) -> float:
    """Return the strongest token-level trigram Dice similarity for typo recall."""
    candidates = {token for token in document_tokens if len(token) >= 4}
    best = 0.0
    for term in query_terms:
        query_grams = _char_ngrams(term)
        if not query_grams:
            continue
        for token in candidates:
            if token == term:
                continue
            token_grams = _char_ngrams(token)
            denominator = len(query_grams) + len(token_grams)
            if denominator:
                similarity = 2 * len(query_grams & token_grams) / denominator
                best = max(best, similarity)
    return best


def _excerpt(text: str, query_terms: list[str]) -> tuple[str, bool, int, int]:
    if len(text) <= _MAX_EXCERPT_CHARS:
        return text, False, 0, len(text)

    folded = text.casefold()
    positions = [folded.find(term) for term in query_terms if term and folded.find(term) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - _MAX_EXCERPT_CHARS // 3)
    end = min(len(text), start + _MAX_EXCERPT_CHARS)
    start = max(0, end - _MAX_EXCERPT_CHARS)
    excerpt = text[start:end]
    if start:
        excerpt = "…" + excerpt
    if end < len(text):
        excerpt += "…"
    return excerpt, True, start, end


def search_documents(
    query: str,
    store: Path,
    limit: int = 8,
    document_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Search canonical blocks locally and return evidence-linked passages.

    This is lexical retrieval only: it does not call an LLM or claim that a
    result answers the question. Evidence IDs are namespaced by document ID
    because block IDs are only unique within a document.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("La query di ricerca non può essere vuota.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("Il limite deve essere un intero compreso tra 1 e 50.")

    terms = _tokens(query)
    if not terms:
        raise ValueError("La query non contiene parole ricercabili.")

    canonical_dir = store / "canonical"
    paths = sorted(canonical_dir.glob("doc_*.json")) if canonical_dir.is_dir() else []
    allowed_ids = set(document_ids) if document_ids else None
    corpus: list[dict[str, Any]] = []

    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        validate_document(document)
        verify_source_integrity(document, store)
        if allowed_ids is not None and document["document_id"] not in allowed_ids:
            continue
        for block in document["blocks"]:
            text = block["normalized_text"]
            tokens = _tokens(text)
            if not tokens:
                continue
            corpus.append({"document": document, "block": block, "tokens": tokens, "length": len(tokens)})

    if not corpus:
        return {"query": query, "results": [], "searched_blocks": 0}

    document_frequency: Counter[str] = Counter()
    for item in corpus:
        document_frequency.update(set(item["tokens"]))

    average_length = sum(item["length"] for item in corpus) / len(corpus)
    query_frequency = Counter(terms)
    ranked: list[tuple[float, str, str, dict[str, Any]]] = []

    for item in corpus:
        frequencies = Counter(item["tokens"])
        score = 0.0
        for term, qf in query_frequency.items():
            tf = frequencies.get(term, 0)
            if not tf:
                continue
            df = document_frequency[term]
            idf = math.log(1 + (len(corpus) - df + 0.5) / (df + 0.5))
            denominator = tf + _K1 * (1 - _B + _B * item["length"] / average_length)
            score += idf * (tf * (_K1 + 1) / denominator) * (1 + math.log(qf))
        char_similarity = _char_similarity(list(query_frequency), item["tokens"])
        if score <= 0 and char_similarity < _MIN_CHAR_DICE:
            continue

        document = item["document"]
        block = item["block"]
        excerpt, truncated, start, end = _excerpt(block["normalized_text"], list(query_frequency))
        locator = dict(block["source_locator"])
        locator["excerpt_char_range"] = [start, end]
        evidence = {
            "evidence_id": f"ev_{document['document_id']}_{block['block_id']}",
            "document_id": document["document_id"],
            "source_id": document["source"]["source_id"],
            "source_filename": document["source"]["original_filename"],
            "source_sha256": document["source"]["sha256"],
            "block_id": block["block_id"],
            "source_locator": locator,
            "score": round(score + char_similarity * 0.05, 6),
            "retrieval_methods": (["bm25"] if score > 0 else []) + (["character_trigram"] if char_similarity >= _MIN_CHAR_DICE else []),
            "text": excerpt,
            "excerpt_truncated": truncated,
            "extraction_warnings": document["extraction_warnings"],
        }
        ranked.append((score + char_similarity * 0.05, document["document_id"], block["block_id"], evidence))

    ranked.sort(key=lambda row: (-row[0], row[1], row[2]))
    return {
        "query": query,
        "results": [row[3] for row in ranked[:limit]],
        "searched_blocks": len(corpus),
    }
