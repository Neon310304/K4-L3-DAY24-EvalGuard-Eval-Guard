"""Read policy Markdown and preserve provenance through hierarchical chunks.

Implemented for this lab against PIPELINE_INTERFACE.md; no prior-lab code is
claimed. Chunk lengths follow the starter's character-size configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re

from config import DATA_DIR, HIERARCHICAL_CHILD_SIZE, HIERARCHICAL_PARENT_SIZE


@dataclass
class Chunk:
    text: str
    metadata: dict
    parent_id: str | None = None


def load_documents() -> list[dict]:
    documents = []
    for path in sorted(Path(DATA_DIR).glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        version = re.search(r"Phiên bản:\s*([^|\n]+)", text)
        effective = re.search(r"Ngày hiệu lực:\s*([^|\n]+)", text)
        documents.append({"text": text, "metadata": {
            "source": path.name, "title": text.splitlines()[0].lstrip("# "),
            "version": version.group(1).strip() if version else "unspecified",
            "effective_date": effective.group(1).strip() if effective else "unspecified",
            "document_sha256": sha256(text.encode()).hexdigest(),
        }})
    if not documents:
        raise ValueError(f"No Markdown policy documents in {DATA_DIR}")
    return documents


def _spans(text: str, limit: int, overlap: int = 0):
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            # Prefer whole sentences/lines, with a minimum of half a window.
            candidates = [text.rfind(mark, start + limit // 2, end)
                          for mark in ("\n", ". ", " ")]
            boundary = next((p for p in candidates if p > start), -1)
            if boundary != -1:
                end = boundary + 1
        yield start, end
        if end == len(text):
            break
        start = max(start + 1, end - overlap)


def chunk_hierarchical(text: str, metadata: dict | None = None):
    metadata = dict(metadata or {})
    parents, children = [], []
    identity = metadata.get("source", "document") + "\0" + text
    prefix = sha256(identity.encode()).hexdigest()[:16]
    for number, (start, end) in enumerate(_spans(text, HIERARCHICAL_PARENT_SIZE)):
        parent_id = f"{prefix}:{number}"
        parent_meta = {**metadata, "chunk_id": parent_id, "start": start, "end": end}
        parents.append(Chunk(text[start:end], parent_meta))
        for child_number, (left, right) in enumerate(
            _spans(text[start:end], HIERARCHICAL_CHILD_SIZE, overlap=48)
        ):
            children.append(Chunk(
                text[start + left:start + right],
                {**metadata, "chunk_id": f"{parent_id}:{child_number}",
                 "start": start + left, "end": start + right}, parent_id,
            ))
    return parents, children
