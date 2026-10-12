from __future__ import annotations

"""Phase A: RAGAS Production Evaluation — 50q, 3 distributions, cluster analysis."""

import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass
from collections.abc import Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH, ANSWERS_PATH, ARTIFACTS_DIR
from src.experiment_support import write_json

Distribution = str  # "factual" | "multi_hop" | "adversarial"

DIAGNOSTIC_TREE = {
    "faithfulness":      ("LLM hallucinating", "Tighten system prompt, lower temperature"),
    "context_recall":    ("Missing relevant chunks", "Improve chunking or add BM25"),
    "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
    "answer_relevancy":  ("Answer doesn't match question", "Improve prompt template"),
}


@dataclass
class RagasResult:
    question_id: int
    distribution: Distribution
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @property
    def avg_score(self) -> float:
        return (self.faithfulness + self.answer_relevancy +
                self.context_precision + self.context_recall) / 4

    @property
    def worst_metric(self) -> str:
        scores = {
            "faithfulness":      self.faithfulness,
            "answer_relevancy":  self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall":    self.context_recall,
        }
        return min(scores, key=scores.get)


# ─── Đã implement sẵn ────────────────────────────────────────────────────────

@dataclass
class RagasEvaluation:
    """Task 2 output: measured rows plus model identifiers reported by m4."""
    results: list[RagasResult]
    evaluator_models: list[str]

def load_test_set_50q(path: str = TEST_SET_PATH) -> list[dict]:
    """Load 50q test set với 3 distributions."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_answers(path: str = ANSWERS_PATH) -> list[dict]:
    """Load pre-generated answers từ setup_answers.py."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"answers_50q.json không tìm thấy tại {path}\n"
            "→ Chạy trước: python scripts/setup_answers.py --live"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict]) -> dict:
    """Provided exporter: preserve the student-produced Task 3 rows verbatim."""
    per_dist: dict[str, dict] = {}
    for dist in ["factual", "multi_hop", "adversarial"]:
        subset = [r for r in results if r.distribution == dist]
        if subset:
            per_dist[dist] = {
                "count": len(subset),
                "faithfulness":      sum(r.faithfulness for r in subset) / len(subset),
                "answer_relevancy":  sum(r.answer_relevancy for r in subset) / len(subset),
                "context_precision": sum(r.context_precision for r in subset) / len(subset),
                "context_recall":    sum(r.context_recall for r in subset) / len(subset),
                "avg_score":         sum(r.avg_score for r in subset) / len(subset),
            }

    report = {
        "total_questions": len(results),
        "per_question": [asdict(r) for r in results],
        "per_distribution": per_dist,
        "failure_clusters": clusters,
        "bottom_10": bottom,
    }
    return report


def save_phase_a_report(results: list[RagasResult], clusters: dict, bottom: list[dict],
                        path: str = os.path.join(ARTIFACTS_DIR, "ragas_50q.json")) -> None:
    write_json(path, build_phase_a_report(results, clusters, bottom))



# ─── Tasks 1-4: Sinh viên implement ──────────────────────────────────────────

def group_by_distribution(test_set: list[dict]) -> dict[str, list[dict]]:
    """Task 1: Nhóm 50 câu hỏi theo 3 distributions.

    Returns:
        {"factual": [...], "multi_hop": [...], "adversarial": [...]}
    """
    groups = {"factual": [], "multi_hop": [], "adversarial": []}
    for item in test_set:
        distribution = item["distribution"]
        if distribution not in groups:
            raise ValueError(f"Unknown distribution: {distribution}")
        groups[distribution].append(item)
    return groups


def run_ragas_50q(answers: list[dict]) -> RagasEvaluation:
    """Task 2: Chạy RAGAS 4 metrics trên toàn bộ 50 câu hỏi.

    Gợi ý — import từ Day 18 của bạn:
        from src.m4_eval import evaluate_ragas

    Steps:
        1. Extract questions, answers, contexts, ground_truths từ answers list
        2. Gọi evaluate_ragas() từ m4_eval.py
        3. Kết hợp kết quả với distribution info từ answers list
        4. Return RagasEvaluation(results, raw["metadata"]["evaluator_models"])
           m4 must report its actual LLM/embedding models; never guess JUDGE_MODEL.
    """
    from src.m4_eval import evaluate_ragas

    raw = evaluate_ragas(
        [a["question"] for a in answers], [a["answer"] for a in answers],
        [a["contexts"] for a in answers], [a["ground_truth"] for a in answers],
    )
    metrics = raw["per_question"]
    if len(metrics) != len(answers):
        raise ValueError("Evaluator must return exactly one row per answer.")
    models = raw.get("metadata", {}).get("evaluator_models")
    if not isinstance(models, list) or not models or any(
        not isinstance(m, str) or not m.strip() for m in models
    ):
        raise ValueError("m4 must report actual evaluator model IDs.")
    results = []
    for answer, row in zip(answers, metrics):
        scores = {}
        for metric in DIAGNOSTIC_TREE:
            value = row[metric] if isinstance(row, Mapping) else getattr(row, metric)
            if isinstance(value, bool):
                raise ValueError(f"Invalid boolean metric: {metric}")
            value = float(value)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"Invalid metric {metric}: {value}")
            scores[metric] = value
        results.append(RagasResult(
            question_id=answer["id"], distribution=answer["distribution"],
            question=answer["question"], answer=answer["answer"],
            contexts=answer["contexts"], ground_truth=answer["ground_truth"], **scores,
        ))
    return RagasEvaluation(results, list(models))


def _diagnose_result(result: RagasResult) -> tuple[str, str]:
    """Content review hints for this HR corpus, not a metric-to-cause classifier.

    Source routing is used only in the evaluation analysis. It never changes
    retrieval, generation, reference answers or measured scores. Missing a file
    in the final contexts does not identify whether search or reranking lost it.
    """
    question = result.question.casefold()
    context_text = "\n".join(result.contexts).casefold()
    sources = list(dict.fromkeys(
        source.strip() for context in result.contexts
        for source in re.findall(r"\[source:\s*([^|\]\n]+)", context)
    ))
    # These are corpus topics to inspect, not canned diagnoses keyed by test IDs.
    routes = [
        (("kết hôn",), ("nghi_phep_dac_biet.md",)),
        (("cha hoặc mẹ",), ("nghi_phep_dac_biet.md",)),
        (("vợ sinh con",), ("nghi_phep_dac_biet.md",)),
        (("lương", "phân loại"), ("ky_luong.md", "phan_loai_du_lieu.md")),
        (("vpn", "khóa"), ("vpn_truy_cap.md",)),
        (("thời gian thử việc",), ("thu_viec.md",)),
        (("đào tạo", "bắt buộc"), ("dao_tao_noi_bo.md",)),
        (("mật khẩu",), ("mat_khau_v2.md",)),
        (("pvi", "thử việc"), ("bao_hiem_suc_khoe.md", "thu_viec.md")),
    ]
    expected = list(dict.fromkeys(
        source for terms, files in routes if all(term in question for term in terms)
        for source in files
    ))
    missing = [source for source in expected if source not in sources]
    abstains = any(phrase in result.answer.casefold() for phrase in (
        "không cung cấp thông tin", "không có thông tin", "không thể xác định",
        "không thể trả lời", "không tìm thấy", "không được đề cập",
    ))
    answer_excerpt = result.answer[:160].replace("\n", " ")
    diagnosis = (
        f"Answer {'chưa trả lời được yêu cầu' if abstains else 'cần đối chiếu từng khẳng định'}: "
        f"«{answer_excerpt}». Reference nêu: «{result.ground_truth}». "
        f"Nguồn trong contexts: {', '.join(sources) or 'không có metadata source'}. "
    )
    if not result.contexts:
        diagnosis += "Không có context làm căn cứ; cần kiểm tra retrieval trước generation."
    elif missing:
        diagnosis += (f"Top contexts thiếu nguồn cần đối chiếu {', '.join(missing)}; "
                      "chưa có log candidates để tách lỗi search khỏi rerank.")
    elif abstains and expected:
        diagnosis += ("Đã lấy đúng tên file nhưng answer chưa đáp ứng; kiểm tra passage "
                      "thiếu điều kiện hay generation bỏ sót căn cứ. Metadata source không "
                      "chứng minh passage đã trả lời được câu hỏi.")
    else:
        diagnosis += (f"{result.worst_metric} thấp nhất chỉ là tín hiệu review, "
                      "chưa đủ quy lỗi cho một module.")
    if ("vpn" in question and "khóa" in question and "12 giờ" in context_text
            and "60 ngày" not in context_text):
        diagnosis += " Đoạn VPN đang nói ngắt phiên sau 12 giờ, không phải khóa tài khoản sau 60 ngày."
    if ("đào tạo" in question and "bắt buộc" in question
            and "dao_tao_noi_bo.md" in sources and "6 tháng đầu" not in context_text):
        diagnosis += " Context đào tạo thiếu nguyên câu quy định nhân viên mới trong 6 tháng đầu."
    if "pvi" in question and "thử việc" in question and "thu_viec.md" in missing:
        diagnosis += " Thiếu exclusion PVI trong chính sách thử việc; không suy ra eligibility từ gói gia đình/bồi hoàn."
    targets = ", ".join(expected) or "các mục chính sách liên quan"
    fix = (f"Với câu hỏi «{result.question}», kiểm tra candidates trước/sau rerank tại {targets}; "
           "thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.")
    if result.distribution == "multi_hop":
        fix += " Thu đủ từng căn cứ trước khi cộng số ngày hoặc suy điều kiện áp dụng."
    if "hiện hành" in result.ground_truth.casefold() and "v1" in result.ground_truth.casefold():
        fix += " Giữ cả v1/v2, chọn phiên bản theo thời điểm được hỏi; không xóa policy cũ."
    return diagnosis, fix


def bottom_10(results: list[RagasResult]) -> list[dict]:
    """Task 3: Lấy 10 câu hỏi có avg_score thấp nhất.

    Returns:
        [{"rank": 1, "question_id": ..., "distribution": ...,
          "question": ..., "avg_score": ..., "worst_metric": ...,
          "diagnosis": ..., "suggested_fix": ...}, ...]
    """
    output = []
    for rank, result in enumerate(sorted(results, key=lambda r: r.avg_score)[:10], 1):
        diagnosis, fix = _diagnose_result(result)
        output.append({
            "rank": rank, "question_id": result.question_id,
            "distribution": result.distribution, "question": result.question,
            "avg_score": round(result.avg_score, 4), "worst_metric": result.worst_metric,
            "diagnosis": diagnosis,
            "suggested_fix": fix,
        })
    return output


def cluster_analysis(results: list[RagasResult]) -> dict:
    """Task 4: Phân tích failure clusters theo (worst_metric × distribution).

    Matrix thống kê worst_metric của mọi câu, không coi mọi câu là một failure.
    Nhóm yếu nhất = distribution có avg_score trung bình thấp nhất (bỏ nhóm rỗng).
    Tổng matrix theo cột chỉ là kích thước nhóm 20/20/10, không đo chất lượng.

    Returns:
        {
          "matrix": {
            "faithfulness":      {"factual": 3, "multi_hop": 5, "adversarial": 2},
            "answer_relevancy":  {...},
            "context_precision": {...},
            "context_recall":    {...},
          },
          "dominant_failure_distribution": "multi_hop",
          "dominant_failure_metric": "context_recall",
          "insight": "..."
        }
    """
    distributions = ("factual", "multi_hop", "adversarial")
    matrix = {m: {d: 0 for d in distributions} for m in DIAGNOSTIC_TREE}
    for result in results:
        matrix[result.worst_metric][result.distribution] += 1
    means = {}
    for distribution in distributions:
        subset = [r for r in results if r.distribution == distribution]
        if subset:
            means[distribution] = sum(r.avg_score for r in subset) / len(subset)
    weakest = min(means, key=means.get) if means else None
    metric = max(matrix, key=lambda m: sum(matrix[m].values())) if results else None
    insight = (
        f"Lowest mean distribution: {weakest} ({means[weakest]:.4f}). "
        f"Most frequent lowest metric: {metric}. Counts cover all questions, not only failures. "
        "Review answer/context/reference for each bottom row before attributing cause. "
        "For abstentions, inspect missing source passages and truncated conditions before changing prompts."
        if results else "No observations; weakest distribution and metric cannot be inferred."
    )
    return {"matrix": matrix, "distribution_avg_scores": means,
            "dominant_failure_distribution": weakest,
            "dominant_failure_metric": metric, "insight": insight}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "a", *sys.argv[1:]]))
