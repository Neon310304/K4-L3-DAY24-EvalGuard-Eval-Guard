"""Offline checks of corpus provenance and adapter failure paths, not live scores."""
import sys
from types import SimpleNamespace

import pytest

from src.m1_chunking import chunk_hierarchical, load_documents
from src.m5_enrichment import enrich_chunks
from src.phase_a_ragas import run_ragas_50q, cluster_analysis
from src.phase_b_judge import cohen_kappa, pairwise_judge
from src import phase_c_guard as guard
from unittest.mock import AsyncMock
import asyncio


def test_corpus_keeps_old_and_current_policies():
    docs = load_documents()
    sources = {doc["metadata"]["source"] for doc in docs}
    assert {"nghi_phep_nam_v2023.md", "nghi_phep_nam_v2024.md",
            "mat_khau_v1.md", "mat_khau_v2.md"} <= sources
    for doc in docs:
        assert len(doc["metadata"]["document_sha256"]) == 64
        parents, children = chunk_hierarchical(doc["text"], doc["metadata"])
        parent_ids = {p.metadata["chunk_id"] for p in parents}
        covered = set()
        for child in children:
            assert child.parent_id in parent_ids
            assert child.metadata["source"] == doc["metadata"]["source"]
            start, end = child.metadata["start"], child.metadata["end"]
            assert child.text == doc["text"][start:end]
            covered.update(range(start, end))
        assert covered == set(range(len(doc["text"])))


def test_enrichment_preserves_order_and_original_content():
    rows = [{"text": "Old policy", "metadata": {"source": "v1.md", "version": "1"}},
            {"text": "Current policy", "metadata": {"source": "v2.md", "version": "2"}}]
    enriched = enrich_chunks(rows)
    assert len(enriched) == len(rows)
    for original, result in zip(rows, enriched):
        assert result.enriched_text.endswith(original["text"])
        assert original["metadata"]["source"] in result.enriched_text
    assert enrich_chunks([]) == []


@pytest.mark.parametrize("metrics,models", [([], ["real"]),
    ([SimpleNamespace(faithfulness=float("nan"), answer_relevancy=.5,
                      context_precision=.5, context_recall=.5)], ["real"]),
    ([SimpleNamespace(faithfulness=.5, answer_relevancy=.5,
                      context_precision=.5, context_recall=.5)], [])])
def test_ragas_rejects_missing_rows_nan_and_unknown_models(monkeypatch, metrics, models):
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(
        evaluate_ragas=lambda *args: {"per_question": metrics,
                                     "metadata": {"evaluator_models": models}}))
    with pytest.raises(ValueError):
        run_ragas_50q([{"id": 1, "distribution": "factual", "question": "Q",
                       "answer": "A", "contexts": ["C"], "ground_truth": "R"}])


@pytest.mark.parametrize("judge,human", [([], []), ([1], [1, 0]), ([True], [1]), ([2], [0])])
def test_kappa_rejects_invalid_labels(judge, human):
    with pytest.raises(ValueError):
        cohen_kappa(judge, human)


def test_empty_clusters_do_not_invent_quality():
    report = cluster_analysis([])
    assert report["distribution_avg_scores"] == {}
    assert report["dominant_failure_distribution"] is None


def test_pairwise_invalid_scores_fail_closed(openai_client):
    openai_client.chat.completions.create.return_value.choices[0].message.content = (
        '{"winner":"A","reasoning":"reason","scores":{"A":true,"B":0.2}}')
    with pytest.raises(ValueError):
        pairwise_judge("Q", "A", "B", "R")


def test_provider_rejection_keeps_distinct_provenance():
    error = RuntimeError("Provider rejected the request")
    error.body = {"error": {"code": "content_filter"}}
    wrapper = RuntimeError(error)
    rails = SimpleNamespace(generate_async=AsyncMock(side_effect=wrapper))
    result = asyncio.run(guard.check_input_rail("untrusted payload", rails))
    assert not result["allowed"]
    assert result["decision_source"] == "provider_content_filter"
    output = asyncio.run(guard.check_output_rail("Q", "sensitive answer", rails))
    assert not output["safe"] and output["final_answer"] != "sensitive answer"
    assert output["flagged_reason"] == "provider_content_filter"


def test_arbitrary_errors_are_not_reported_as_rail_blocks():
    rails = SimpleNamespace(generate_async=AsyncMock(side_effect=RuntimeError(
        "content_filter appears in untrusted error text")))
    with pytest.raises(RuntimeError):
        asyncio.run(guard.check_input_rail("Q", rails))
