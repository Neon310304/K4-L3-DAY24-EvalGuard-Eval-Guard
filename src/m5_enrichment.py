"""Deterministic source enrichment; preserve all original text and chunk order."""
from dataclasses import dataclass


@dataclass
class EnrichedChunk:
    enriched_text: str
    auto_metadata: dict


def enrich_chunks(chunks: list[dict]) -> list[EnrichedChunk]:
    enriched = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        header = " | ".join(f"{key}: {metadata[key]}" for key in
                            ("source", "title", "version", "effective_date") if key in metadata)
        enriched.append(EnrichedChunk(
            f"[{header}]\n{chunk['text']}" if header else chunk["text"],
            {"enrichment": "source_metadata_only"},
        ))
    return enriched
