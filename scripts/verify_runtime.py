"""Check imports and optionally rebuild/probe retrieval; never call a paid API."""
import argparse
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, QDRANT_HOST, QDRANT_PORT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-pipeline", action="store_true",
                        help="Rebuild the Qdrant collection and probe search/rerank using cached models.")
    args = parser.parse_args()
    print(f"Python: {platform.python_version()}; OS: {platform.platform()}")
    for package, module in [("ragas", "ragas"), ("nemoguardrails", "nemoguardrails"),
                            ("presidio-analyzer", "presidio_analyzer"), ("spacy", "spacy"),
                            ("sentence-transformers", "sentence_transformers"),
                            ("pyarrow", "pyarrow"), ("numpy", "numpy")]:
        import_module(module)
        print(f"Import OK: {package}=={version(package)}")
    import spacy
    spacy.load("en_core_web_lg")
    print("spaCy en_core_web_lg: loaded")
    from qdrant_client import QdrantClient
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print(f"Qdrant connected; collections={len(client.get_collections().collections)}")
    client.close()
    print(f"API endpoint: {OPENAI_BASE_URL}; key configured: {bool(OPENAI_API_KEY)}")
    if args.with_pipeline:
        from scripts.setup_answers import build_pipeline
        from src.experiment_support import read_json
        from config import TEST_SET_PATH
        search, reranker, top_k = build_pipeline()
        question = read_json(TEST_SET_PATH)[0]["question"]
        results = search.search(question)
        if not results:
            raise ValueError("Retrieval returned no candidates.")
        docs = [{"text": r.text, "score": r.score, "metadata": r.metadata} for r in results]
        ranked = reranker.rerank(question, docs, top_k=top_k)
        originals = {r.metadata["chunk_id"]: r for r in results}
        if not ranked or len(ranked) > top_k:
            raise ValueError("Reranker returned an invalid result count.")
        for row in ranked:
            original = originals[row.metadata["chunk_id"]]
            if row.text != original.text or row.metadata != original.metadata:
                raise ValueError("Reranking changed source text or metadata.")
            if not row.metadata.get("parent_id") or not row.metadata.get("source"):
                raise ValueError("Missing chunk provenance.")
        print(f"Pipeline OK: {len(search.chunks)} indexed chunks; {len(results)} search candidates; "
              f"{len(ranked)} reranked contexts; source/parent metadata preserved")


if __name__ == "__main__":
    main()
