"""Student contracts; no RAGAS API calls."""
from types import SimpleNamespace
import sys
from unittest.mock import Mock

import pytest

from src.phase_a_ragas import (load_test_set_50q, group_by_distribution, run_ragas_50q,
                               bottom_10, cluster_analysis, RagasResult)

pytestmark = pytest.mark.student


@pytest.fixture
def dummy_results():
    return [RagasResult(i+1, dist, f"Q{i}", "A", ["C"], "GT", *scores)
            for i, (dist, scores) in enumerate([
                ("factual", (.9,.8,.7,.6)), ("multi_hop", (.3,.4,.5,.2)),
                ("adversarial", (.1,.2,.3,.4)), ("factual", (.8,.7,.9,.8)),
                ("multi_hop", (.2,.3,.1,.2))])]


def test_group_exact_counts():
    groups = group_by_distribution(load_test_set_50q())
    assert set(groups) == {"factual","multi_hop","adversarial"}
    assert [len(groups[d]) for d in ("factual","multi_hop","adversarial")] == [20,20,10]


def test_ragas_adapter_preserves_rows(monkeypatch):
    questions = load_test_set_50q()
    answers = [{**q, "answer": "A", "contexts": ["C"]} for q in questions]
    metrics = [SimpleNamespace(faithfulness=.8, answer_relevancy=.7,
                               context_precision=.6, context_recall=.5) for _ in answers]
    evaluator_models = ["evaluator-test", "embedding-test"]
    evaluate = Mock(return_value={"per_question": metrics,
                                  "metadata": {"evaluator_models": evaluator_models}})
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(evaluate_ragas=evaluate))
    evaluation = run_ragas_50q(answers)
    results = evaluation.results
    assert evaluation.evaluator_models == evaluator_models
    assert len(results) == 50
    assert [r.question_id for r in results] == [q["id"] for q in questions]
    assert results[0].faithfulness == .8
    evaluate.assert_called_once()
    assert list(evaluate.call_args.args[0]) == [q["question"] for q in questions]


def test_bottom_nonempty_sorted_complete(dummy_results):
    rows = bottom_10(dummy_results)
    assert len(rows) == 5
    assert [r["rank"] for r in rows] == [1,2,3,4,5]
    assert [r["avg_score"] for r in rows] == sorted(r["avg_score"] for r in rows)
    assert rows[0]["question_id"] == 5
    for row in rows:
        assert {"question_id","distribution","question","worst_metric",
                "diagnosis","suggested_fix"} <= row.keys()
        assert row["diagnosis"].strip() and row["suggested_fix"].strip()


def test_bottom_capped_at_ten(dummy_results):
    repeated = [RagasResult(i+1,r.distribution,r.question,r.answer,r.contexts,r.ground_truth,
                           r.faithfulness,r.answer_relevancy,r.context_precision,r.context_recall)
                for i,r in enumerate(dummy_results*4)]
    assert len(bottom_10(repeated)) == 10


def test_cluster_matrix(dummy_results):
    result = cluster_analysis(dummy_results)
    assert result["matrix"] == {
        "faithfulness":{"factual":0,"multi_hop":0,"adversarial":1},
        "answer_relevancy":{"factual":1,"multi_hop":0,"adversarial":0},
        "context_precision":{"factual":0,"multi_hop":1,"adversarial":0},
        "context_recall":{"factual":1,"multi_hop":1,"adversarial":0}}
    assert result["dominant_failure_metric"] == "context_recall"
    assert result["insight"].strip()


def test_weakest_distribution_is_quality_not_size():
    results = []
    for dist,count,value in [("factual",20,.95),("multi_hop",20,.70),("adversarial",10,.10)]:
        for _ in range(count):
            results.append(RagasResult(len(results)+1,dist,"Q","A",["C"],"GT",
                                       value,value,value,value))
    assert cluster_analysis(results)["dominant_failure_distribution"] == "adversarial"


def test_bottom_diagnosis_reads_answer_context_and_reference():
    result = RagasResult(
        16, "factual", "Tài khoản VPN bị khóa sau bao nhiêu ngày?",
        "Context chỉ nói phiên VPN ngắt sau 12 giờ, không có thông tin.",
        ["[source: vpn_truy_cap.md] Phiên VPN tự động ngắt sau 12 giờ."],
        "Tài khoản VPN tự động bị khóa sau 60 ngày không hoạt động.",
        .5, .0, .0, .0,
    )
    row = bottom_10([result])[0]
    assert result.ground_truth in row["diagnosis"]
    assert "12 giờ" in row["diagnosis"]
    assert "vpn_truy_cap.md" in row["suggested_fix"]


def test_ragas_mapping_rows_keep_scores_aligned(monkeypatch):
    from collections import UserDict
    from decimal import Decimal

    questions = load_test_set_50q()[:2]
    answers = [{**q, "answer": f"A{q['id']}", "contexts": [f"C{q['id']}"]} for q in questions]
    metric_names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    metrics = [UserDict({name: Decimal(value) for name in metric_names}) for value in ("0.2", "0.9")]
    evaluate = Mock(return_value={"per_question": metrics,
                                  "metadata": {"evaluator_models": ["evaluator", "embedding"]}})
    monkeypatch.setitem(sys.modules, "src.m4_eval", SimpleNamespace(evaluate_ragas=evaluate))
    evaluation = run_ragas_50q(answers)
    assert [r.question_id for r in evaluation.results] == [q["id"] for q in questions]
    assert [r.answer for r in evaluation.results] == [a["answer"] for a in answers]
    assert [r.contexts for r in evaluation.results] == [a["contexts"] for a in answers]
    assert [r.faithfulness for r in evaluation.results] == [.2, .9]
    assert all(type(getattr(r, name)) is float for r in evaluation.results for name in metric_names)
