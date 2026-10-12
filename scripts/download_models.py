"""Cache the configured retrieval/reranking models; no paid API calls."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import EMBEDDING_MODEL, RERANK_MODEL


if __name__ == "__main__":
    from huggingface_hub import snapshot_download
    from flashrank import Ranker
    path = snapshot_download(EMBEDDING_MODEL,
                             allow_patterns=["*.json", "*.model", "pytorch_model.bin"],
                             max_workers=4)
    print(f"Cached embedding model: {EMBEDDING_MODEL} at {path}")
    Ranker(model_name=RERANK_MODEL, cache_dir=str(Path.home() / ".cache" / "flashrank"))
    print(f"Cached reranking model: {RERANK_MODEL}")
