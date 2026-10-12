"""BGE-M3 dense retrieval in Qdrant + BM25, fused by reciprocal ranks."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from config import (BM25_TOP_K, COLLECTION_NAME, DENSE_TOP_K, EMBEDDING_MODEL,
                    HYBRID_TOP_K, QDRANT_HOST, QDRANT_PORT)


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())


class HybridSearch:
    def __init__(self):
        from qdrant_client import QdrantClient
        from transformers import AutoModel, AutoTokenizer
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=120)
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        self.encoder = AutoModel.from_pretrained(EMBEDDING_MODEL).eval()
        self.chunks = []
        self.bm25 = None

    def _encode(self, texts: list[str]):
        """BGE-M3 dense representation: L2-normalized CLS embeddings."""
        import torch
        vectors = []
        with torch.inference_mode():
            for start in range(0, len(texts), 8):
                tokens = self.tokenizer(texts[start:start + 8], padding=True,
                                        truncation=True, max_length=512, return_tensors="pt")
                hidden = self.encoder(**tokens).last_hidden_state[:, 0]
                vectors.extend(torch.nn.functional.normalize(hidden, p=2, dim=1).cpu().tolist())
        return vectors

    def index(self, chunks: list[dict]):
        from qdrant_client.models import Distance, PointStruct, VectorParams
        from rank_bm25 import BM25Okapi
        if not chunks:
            raise ValueError("Cannot index an empty corpus.")
        self.chunks = list(chunks)
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
        vectors = self._encode([c["text"] for c in chunks])
        self.client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )
        for start in range(0, len(chunks), 64):
            self.client.upsert(collection_name=COLLECTION_NAME, wait=True, points=[
                PointStruct(id=i, vector=vectors[i], payload=chunks[i])
                for i in range(start, min(start + 64, len(chunks)))
            ])

    def search(self, question: str) -> list[SearchResult]:
        if self.bm25 is None:
            raise ValueError("Call index() before search().")
        vector = self._encode([question])[0]
        dense = self.client.search(collection_name=COLLECTION_NAME, query_vector=vector,
                                   limit=DENSE_TOP_K)
        lexical = self.bm25.get_scores(tokenize(question))
        ranked = sorted(range(len(self.chunks)), key=lambda i: float(lexical[i]), reverse=True)
        scores = {}
        for rank, hit in enumerate(dense, 1):
            scores[int(hit.id)] = scores.get(int(hit.id), 0.0) + 1 / (60 + rank)
        for rank, index in enumerate(ranked[:BM25_TOP_K], 1):
            if lexical[index] > 0:
                scores[index] = scores.get(index, 0.0) + 1 / (60 + rank)
        return [SearchResult(self.chunks[i]["text"], score, dict(self.chunks[i]["metadata"]))
                for i, score in sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))[:HYBRID_TOP_K]]
