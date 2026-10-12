"""Multilingual cross-encoder reranking without reference/test-label access."""
from config import RERANK_MODEL
from src.m2_search import SearchResult
from pathlib import Path


class CrossEncoderReranker:
    def __init__(self):
        from flashrank import Ranker
        self.model = Ranker(model_name=RERANK_MODEL,
                            cache_dir=str(Path.home() / ".cache" / "flashrank"))

    def rerank(self, question: str, docs: list[dict], top_k: int = 3) -> list[SearchResult]:
        if not docs or top_k <= 0:
            return []
        from flashrank import RerankRequest
        passages = [{"id": i, "text": doc["text"]} for i, doc in enumerate(docs)]
        ranked = self.model.rerank(RerankRequest(query=question, passages=passages))
        return [SearchResult(docs[row["id"]]["text"], float(row["score"]),
                             dict(docs[row["id"]]["metadata"])) for row in ranked[:top_k]]
