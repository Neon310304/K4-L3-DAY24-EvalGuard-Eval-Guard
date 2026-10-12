"""Produce reviewable Markdown from validated live artifacts, never mock scores.

Rerunning this command replaces the three generated reports. Interpretations
remain hypotheses until the included answer/context/reference evidence is read.
"""
from __future__ import annotations

import json
import hashlib
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import ROOT_DIR
from src.experiment_support import read_json
from src.report_contracts import (validate_answers, validate_metadata, validate_phase_a,
                                  validate_phase_b, validate_phase_c)


ROOT = Path(ROOT_DIR)
AUTHOR = "Trần Quốc Vượng — 2A202602522"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows])


def details(value):
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def provenance(report):
    meta = report["metadata"]
    return (f"Người phụ trách: {AUTHOR}.\n\n"
            f"Run timestamp (UTC): {meta['created_at']}; run_kind: {meta['run_kind']}.\n\n"
            "Model IDs theo vai trò (cấu hình/ID provider ghi lại, không mặc nhiên xác nhận snapshot):\n\n" +
            details(meta["models"]) + "\n")


def phase_a_report(report, answers):
    distributions = ("factual", "multi_hop", "adversarial")
    metrics = ("faithfulness", "answer_relevancy", "context_precision", "context_recall", "avg_score")
    clusters = report["failure_clusters"]
    by_id = {r["question_id"]: r for r in report["per_question"]}
    fallback = sum(a["generation_mode"] == "extractive_fallback" for a in answers)
    text = "# Phân tích lỗi Phase A\n\n" + provenance(report)
    text += (f"Nguồn: `artifacts/ragas_50q.json`, `artifacts/answers_50q.json`. "
             f"Có {len(answers)} answers; {len(answers) - fallback} LLM, {fallback} extractive fallback. "
             "Contexts lấy từ BGE-M3/BM25/Qdrant và FlashRank, không lấy từ ground truth. "
             "M4 gọi RAGAS 0.1.22 với bốn metric thật; không thay NaN bằng số giả. "
             "Điểm và metadata giữ từ batch live; bottom/matrix/diagnosis được dựng lại từ "
             "per_question đã lưu. Các gợi ý nguồn theo chủ đề trong Task 3 chỉ phục vụ review, "
             "không tham gia retrieval/generation.\n\n")
    text += "## Điểm theo distribution\n\n" + table(
        ["Metric", "factual (20)", "multi_hop (20)", "adversarial (10)"],
        [[m] + [f"{report['per_distribution'][d][m]:.6f}" for d in distributions] for m in metrics])
    text += "\n\n## Bottom 10 và bằng chứng\n\n" + table(
        ["Rank", "ID", "Question", "Distribution", "Mean", "Worst metric", "Diagnosis", "Fix"],
        [[r[k] for k in ("rank", "question_id", "question", "distribution", "avg_score",
                         "worst_metric", "diagnosis", "suggested_fix")] for r in report["bottom_10"]])
    text += ("\n\nDiagnosis theo metric là giả thuyết cần đối chiếu. Faithfulness thấp gợi ý "
             "answer chưa được contexts hỗ trợ; recall thấp gợi ý thiếu căn cứ; precision thấp "
             "gợi ý chunks không hữu ích; relevancy thấp gợi ý trả lời lệch hoặc thiếu yêu cầu. "
             "Không coi metric đơn lẻ là bằng chứng đủ để kết luận nguyên nhân.\n")
    for bottom in report["bottom_10"]:
        row = by_id[bottom["question_id"]]
        text += f"\n### Câu {row['question_id']} — {row['distribution']}\n\n"
        text += table(["faithfulness", "answer_relevancy", "context_precision", "context_recall"],
                      [[f"{row[m]:.6f}" for m in metrics[:4]]]) + "\n\n"
        text += f"Câu hỏi: {row['question']}\n\nAnswer thực tế:\n\n> {row['answer']}\n\n"
        text += f"Reference:\n\n> {row['ground_truth']}\n\nContexts đã retrieve/rerank:\n\n"
        text += details(row["contexts"]) + "\n"
        text += f"\nĐối chiếu nội dung (Task 3): {bottom['diagnosis']}\n\n"
        text += f"Hướng sửa cần thử: {bottom['suggested_fix']}\n"
    text += "\n## Matrix và nhóm yếu nhất\n\n" + table(
        ["Worst metric", *distributions], [[m] + [clusters["matrix"][m][d] for d in distributions]
                                          for m in clusters["matrix"]])
    weakest = clusters["dominant_failure_distribution"]
    text += (f"\n\nNhóm yếu nhất theo mean: **{weakest}**, "
             f"{clusters['distribution_avg_scores'][weakest]:.6f}. "
             f"Worst metric thường gặp nhất: **{clusters['dominant_failure_metric']}**. "
             "Tổng cột 20/20/10 là kích thước mẫu, không đo chất lượng; mọi câu được đếm một lần.\n\n")
    a = report["per_distribution"]["adversarial"]["avg_score"]
    f = report["per_distribution"]["factual"]["avg_score"]
    text += ("## Bẫy adversarial, cải tiến và giới hạn\n\n"
             f"Adversarial mean {a:.6f}, factual mean {f:.6f}; "
             f"điều kiện adversarial < factual: {a < f}. "
             "Corpus giữ nghỉ phép 2023/2024 và mật khẩu v1/v2. Đối chiếu số ngày phép, "
             "độ dài/chu kỳ mật khẩu và các phủ định trong evidence ở trên; điểm thấp hơn "
             "không tự chứng minh hệ thống nhận ra xung đột phiên bản.\n\n"
             "Ưu tiên thử chunk theo mục để giữ trọn điều kiện thay vì cắt giữa câu; "
             "thêm version/effective-date metadata filtering theo thời điểm được hỏi mà vẫn giữ "
             "tài liệu lịch sử; thử top-k lớn hơn cho multi-hop rồi rerank và deduplicate. "
             "Đổi từng yếu tố một, sinh lại answers và chạy RAGAS để so từng ID, không sửa test set. "
             "50 câu và một lượt model chưa đủ suy rộng sang production; RAGAS cũng có sai số judge.\n")
    # Review this saved batch, rather than turning its metric labels into causes.
    reviewed_answers_hash = "db39b713f8872579f5d05641272608595f6ef61f2002def3585095b7cb34a0e9"
    if report["metadata"]["source_sha256"]["answers_50q.json"] == reviewed_answers_hash:
        text += (
            "\n## Đọc lỗi từ evidence của batch này\n\n"
            "- **IDs 1/8/9/26 — thiếu chính sách nghỉ đặc biệt.** Ba contexts của mỗi câu "
            "không có `nghi_phep_dac_biet.md`. File gốc ghi kết hôn 3 ngày, tang lễ 3 ngày, "
            "nam có vợ sinh con 5 ngày và con kết hôn 1 ngày. Answer đều nói thiếu thông tin. "
            "Đây là bằng chứng thiếu căn cứ ở top contexts, chưa đủ tách lỗi search/rerank. "
            "Cần trace vị trí các chunks này trước/sau rerank, thay vì chỉ đổi prompt. "
            "Với ID 26, reference cộng 3+1=4; câu 'phép đặc biệt không cộng dồn' ở cuối corpus "
            "cần người quản lý policy làm rõ phạm vi áp dụng khi mở rộng đánh giá. Giữ reference "
            "được cấp cho lượt chấm hiện tại.\n"
            "- **ID 6 — thiếu cầu nối giữa lương và phân loại.** Context 1 có bảng cấp 3 Bí mật, "
            "nhưng không có câu 'Thông tin lương là dữ liệu Bí mật' trong `ky_luong.md`. "
            "Chỉ bảng phân loại chưa xác định lương ở cấp nào. Faithfulness thấp không tự chứng minh "
            "answer đã bịa cấp độ; answer thực tế từ chối xác định. Hướng sửa là lấy cả quy chế "
            "lương và quy tắc xử lý dữ liệu, rồi đối chiếu từng khẳng định.\n"
            "- **ID 16 — nhầm loại đoạn VPN.** Context 1 nói ngắt phiên sau 12 giờ; "
            "điều cần hỏi là khóa tài khoản sau 60 ngày không hoạt động trong cùng file. "
            "Hai contexts còn lại về tạm ứng/mật khẩu cũ không bù được đoạn thiếu. Thử mở rộng "
            "parent hoặc retrieve theo mục quản lý tài khoản.\n"
            "- **ID 19 — thiếu hẳn nguồn thời gian thử việc.** Contexts là công tác phí, phép năm "
            "và Mentor/Buddy; không có `thu_viec.md` với 60 ngày tiêu chuẩn/90 ngày cho Manager. "
            "Không thể khắc phục chỉ bằng yêu cầu LLM trả lời chắc hơn khi passage chưa được lấy.\n"
            "- **ID 32 — mất đầu điều kiện trong chunk.** Context 1 bắt đầu 'ổi đào tạo của phòng ban' "
            "rồi chuyển sang ngân sách; câu đầy đủ ở `dao_tao_noi_bo.md` quy định nhân viên mới "
            "trong 6 tháng đầu bắt buộc tham gia. Child chunk theo ký tự làm mất điều kiện này; "
            "đây là ví dụ cụ thể cho thử parent expansion/chunk theo mục. Answer còn suy từ phần "
            "ngân sách thành kết luận policy không quy định đào tạo nội bộ; cần giới hạn phát biểu "
            "ở contexts đã thấy, thay vì khẳng định về toàn bộ tài liệu.\n"
            "- **ID 43 — thiếu retrieval trước khi kiểm tra version.** Top contexts không có "
            "`mat_khau_v1.md` hoặc `mat_khau_v2.md`, nên lượt này chưa chứng minh LLM chọn nhầm "
            "8 thay vì 12 ký tự; answer đã không đưa ra con số. Sau khi lấy được đúng passage, "
            "mới kiểm tra ưu tiên v2 hiện hành mà vẫn giữ v1 để trả lời câu lịch sử.\n"
            "- **ID 48 — thiếu exclusion PVI.** Contexts lấy gói gia đình, bồi hoàn và nghỉ ốm. "
            "Điều 'thử việc chưa được hưởng gói PVI' nằm trong `thu_viec.md`, không được lấy. "
            "Answer từ chối, không phải trả lời sai rằng thử việc được PVI; cần phân biệt thiếu "
            "căn cứ phủ định với đảo phủ định.\n\n"
            "**Đối chiếu bẫy ngoài bottom 10:** ID 44 có cả v1/v2 trong contexts và answer chọn "
            "120 ngày theo v2; đây là một lần xử lý xung đột phiên bản thành công. IDs 41/42 "
            "chọn 15 ngày và quy tắc 3 năm theo bản 2024. ID 45 trả lời MFA bắt buộc, ID 47 "
            "giữ phủ định không tự xử lý malware. Ngược lại, ID 49 đã lấy cả hai phiên bản phép "
            "nhưng answer bỏ số 12 ngày của bản 2023; IDs 46/50 chưa trả lời được phủ định/cấm "
            "mà reference yêu cầu. Vì vậy adversarial mean thấp hơn factual chỉ là mô tả "
            "batch, không chứng nhận mọi bẫy đã được giải quyết.\n\n"
            "**Thứ tự cải tiến:** trace search/rerank cho nhóm nghỉ đặc biệt và thử việc; "
            "thử parent expansion/chunk theo heading cho VPN và đào tạo; bổ sung retrieval "
            "nhiều nguồn cho lương/PVI; sau đó đánh giá version filtering trên cả câu hiện hành "
            "và lịch sử. Đo từng thay đổi bằng batch mới có nguồn riêng; batch hiện tại vẫn là baseline.\n"
        )
    else:
        text += ("\nPhân tích chi tiết của batch baseline chưa áp dụng cho answers hash mới; "
                 "cần đọc lại từng bottom row trước khi kết luận nguyên nhân.\n")
    return text


def phase_b_report(report, humans):
    text = "# Đánh giá LLM Judge Phase B\n\n" + provenance(report)
    text += ("Nguồn: `artifacts/judge_results.json`. A lấy đúng answer pipeline; B lấy đúng "
             "model_answer của human fixture; reference lấy ground_truth của test set. "
             "Năm IDs cố định: 1, 5, 12, 21, 41; hai lượt/cặp, lượt hai quy về A/B gốc.\n\n"
             "Nguồn candidates/reference đã đối chiếu bằng nội dung và SHA256:\n\n")
    text += details(report["pair_sources"]) + "\n\n" + details(report["metadata"]["source_sha256"])
    text += ("\n\n`winner_pass2` và `scores_pass2` đã quy về A/B gốc. "
             "`reasoning_pass2` giữ nguyên lời API theo thứ tự swapped: local A = B gốc, "
             "local B = A gốc. Khi đọc reasoning lượt hai cần đổi danh tính theo quy tắc này.\n\n"
             "## Năm cặp và hai lượt\n\n")
    text += table(["ID", "Pass 1", "Pass 2 (gốc)", "Final", "Consistent", "Scores 1", "Scores 2"],
                  [[r[k] for k in ("question_id", "winner_pass1", "winner_pass2", "final_winner",
                                   "position_consistent", "scores_pass1", "scores_pass2")]
                   for r in report["pairwise_results"]])
    for row in report["pairwise_results"]:
        text += f"\n\n### Cặp {row['question_id']}\n\n" + details(row)
    bias = report["bias_report"]
    text += "\n\n## Position và verbosity\n\n" + details(bias)
    counts = bias["verbosity_details"]
    text += (f"\n\nPosition inconsistency = {bias['position_bias_count']}/{bias['total_judged']} "
             f"= {bias['position_bias_rate']:.6f}. Winner dài hơn: "
             f"A thắng và dài hơn {counts['a_wins_a_longer']} cặp; "
             f"B thắng và dài hơn {counts['b_wins_b_longer']} cặp; "
             f"tổng decisive {counts['total_decisive']}; "
             f"verbosity rate = {bias['verbosity_bias']:.6f}.\n")
    text += ("\n\nBất đồng sau swap chỉ cho thấy nhạy với thứ tự/lượt gọi; chưa xác định "
             "nguyên nhân. Verbosity là tỷ lệ winner dài hơn theo số ký tự trong các lượt decisive; "
             "answer dài có thể thắng vì đủ ý. Cần đọc reference và reasoning của từng cặp "
             "trước khi gán thiên lệch. Tie không được đổi thành nhãn tốt/xấu.\n\n"
             "## Calibration đúng model_answer\n\n"
             "Binary helper chỉ nhận question, model_answer gốc và reference; human_label, "
             "human_note và tỷ lệ nhãn không được gửi vào prompt. Nhãn người chỉ dùng sau "
             "khi đã tạo đủ mười binary judgments.\n\n")
    labels = {r["question_id"]: r["human_label"] for r in humans}
    text += table(["ID", "Model answer gốc", "Judge", "Human", "Agree", "Reasoning"],
                  [[r["question_id"], r["model_answer"], r["label"], labels[r["question_id"]],
                    r["label"] == labels[r["question_id"]], r["reasoning"]]
                   for r in report["binary_judgments"]])
    calibration = report["calibration"]
    j, h = calibration["judge_labels"], calibration["human_labels"]
    n = len(j)
    observed = sum(x == y for x, y in zip(j, h)) / n
    chance = sum(j.count(v) * h.count(v) for v in (0, 1)) / n**2
    text += (f"\n\nObserved agreement p_o={observed:.6f}; chance agreement p_e={chance:.6f}. "
             f"κ=(p_o-p_e)/(1-p_e)=**{calibration['cohen_kappa']:.6f}**. "
             f"Điều kiện bonus κ>0.6: {calibration['cohen_kappa'] > .6}.\n\n"
             f"Judge có {j.count(1)} nhãn 1/{j.count(0)} nhãn 0; "
             f"human có {h.count(1)} nhãn 1/{h.count(0)} nhãn 0. "
             f"p_e=({j.count(1)}/{n} × {h.count(1)}/{n}) + "
             f"({j.count(0)}/{n} × {h.count(0)}/{n}). IDs/thứ tự: "
             f"{calibration['question_ids']}.\n\n")
    text += table(["Judge \\ Human", "0", "1"], [
        [str(label)] + [sum(x == label and y == target for x, y in zip(j, h))
                        for target in (0, 1)] for label in (0, 1)])
    text += ("\n\n## Đọc nội dung và độ tin cậy của reasoning\n\n"
             "Độ dài tính bằng `len(str)` của Python, gồm khoảng trắng và Markdown. "
             "Độ dài không phải tiêu chí độc lập để đổi winner.\n\n")
    # Fixed qualitative observations belong to this measured report, including
    # its labels/reasoning, rather than any future rerun on the same inputs.
    reviewed_report_hash = "abdb0cb266f86c4c197414fcc3b58592b71ebc14e6be7b350ab6815e2d5cbdc4"
    report_hash = hashlib.sha256(json.dumps(report, ensure_ascii=False, sort_keys=True)
                                 .encode("utf-8")).hexdigest()
    if report_hash == reviewed_report_hash:
        pairs = {row["question_id"]: row for row in report["pairwise_results"]}
        reviews = [
            (1, "B đúng 3 ngày; A từ chối trả lời",
             "B ngắn hơn nhưng đủ ý chính; pairwise không nhận contexts nên chưa thể kết luận A nói sai về contexts đã retrieve."),
            (5, "A đúng CEO; B nhầm giám đốc phòng ban",
             "A dài hơn và thắng vì đúng ngưỡng phê duyệt."),
            (12, "B nêu mức tối thiểu 1 tháng; A bỏ sót mức tối thiểu",
             "A dài hơn nhưng thiếu số tiền cần hỏi; phần trọng số hiệu suất không bù được ý thiếu."),
            (21, "B đủ 18 ngày và lương 20–35 triệu; A bỏ sót khoảng lương",
             "B thắng hợp lý; reasoning pass 2 gọi A gốc accurate cả về lương dù A không đưa khoảng lương."),
            (41, "A dùng v2024 là 15 ngày; B dùng v2023 là 12 ngày",
             "A dài hơn và thắng vì đúng phiên bản; chưa tách được hiệu ứng độ dài khỏi nội dung."),
        ]
        text += table(
            ["ID", "Đối chiếu reference", "Winner", "Độ dài A/B", "Nhận xét kiểm chứng"],
            [[qid, comparison, pairs[qid]["final_winner"],
              f"{len(pairs[qid]['answer_a'])}/{len(pairs[qid]['answer_b'])}", note]
             for qid, comparison, note in reviews])
        text += (
            "\n\nỞ lượt hai, API nhận thứ tự B/A. Trường `winner_pass2` và `scores_pass2` "
            "đã được quy về danh tính A/B ban đầu, còn `reasoning_pass2` được lưu nguyên văn "
            "của lượt swapped nên các từ ‘Answer A/B’ trong đoạn reasoning đó chỉ vị trí của "
            "lượt hai. Ví dụ ở ID 1, reasoning pass 2 gọi local A là câu 3 ngày; đó là B gốc. "
            "Không có cặp bất đồng sau quy đổi (0/5), vì vậy batch này không cho một ví dụ live "
            "về tie do swap; test `test_swap_conversion_and_calls` kiểm tra trường hợp bất đồng.\n\n"
            "Reasoning nhị phân cần đối chiếu từng mệnh đề: "
            "ID 1 có judge=human=1, nhưng reasoning nói answer nêu điều kiện ‘không trừ vào phép năm’ "
            "mà model_answer gốc không viết điều đó. ID 46 cũng có judge=human=1, nhưng reasoning nói "
            "answer đã nêu phê duyệt trưởng phòng; answer gốc chỉ nói nghỉ không lương. Các lệch "
            "mô tả này không đổi nhãn đã đo. Riêng ID 46 cần người review xác định phê duyệt "
            "trưởng phòng có là điều kiện thiết yếu theo rubric hay không; cả human và judge "
            "đồng ý 1 vẫn có thể cùng bỏ sót một điều kiện.\n\n"
            "ID 29 có judge=human=0; reference yêu cầu cả Trưởng phòng và Kế toán trưởng, "
            "cùng phí 2% × 8.000.000 × 15/30 = 80.000 VNĐ. Model_answer thiếu người duyệt thứ hai "
            "và số tiền pro-rata. Reasoning nói phí không phải 2% trên tổng tạm ứng dễ gây nhầm: "
            "8 triệu vẫn là gốc tính phí, thiếu sót là thời gian 15 ngày và kết quả cụ thể. "
            "Không có binary case bất đồng nhãn; các lỗi mô tả cho thấy κ chỉ đo agreement "
            "với nhãn người trên tập này, không chứng minh rationale luôn bám từng mệnh đề.\n\n"
            f"Nhận xét thủ công gắn fingerprint toàn bộ JSON (serialize sort_keys=True, "
            f"ensure_ascii=False, UTF-8): `{report_hash}`. Khi runner ghi batch khác, cần review lại.\n\n"
        )
    else:
        text += ("Nhận xét thủ công chưa áp dụng vì nội dung batch hoặc metadata đã thay đổi; "
                 "cần đọc lại candidates, reference và reasoning trước khi kết luận.\n\n")
    text += (
             "## Giới hạn và cách dùng judge\n\n"
             "Chỉ có năm cặp và mười nhãn; κ trên mẫu nhỏ không chứng minh judge đúng cho "
             "mọi chính sách. Ground truth và human labels cũng cần được review khi có bất đồng. "
             "Giữ swap-and-average, reference và temperature=0; lưu model/prompt khi so sánh các "
             "lần chạy. Dùng judge để ưu tiên review, kết hợp người đọc các case thiếu điều kiện, "
             "phủ định hoặc sai phiên bản trước quyết định triển khai.\n")
    return text


def blueprint(a, b, c):
    latency = c["latency"]
    overall = sum(r["faithfulness"] for r in a["per_question"]) / len(a["per_question"])
    avg = sum(sum(r[m] for m in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")) / 4
              for r in a["per_question"]) / len(a["per_question"])
    text = "# Blueprint CI/CD cho RAG và guardrails\n\n" + provenance(c)
    text += ("Đây là **đề xuất CI/CD**; chưa tạo/chạy workflow CI. "
             "Nguồn: ba JSON live trong `artifacts/`. Generation/evaluator từ A, judge từ B:\n\n" +
             details({"A": a["metadata"]["models"], "B": b["metadata"]["models"]}) +
             "\n\n## Kiến trúc và failure action\n\n"
             "Input → Presidio → NeMo input → RAG → NeMo output → response. "
             "Presidio phát hiện CCCD/CMND, điện thoại và email, chặn input có PII; "
             "NeMo self-check chặn jailbreak, extraction và ngoài phạm vi. RAG dùng chunk "
             "có source/version/date → BM25+BGE-M3/Qdrant → multilingual FlashRank → generation "
             "bám context. NeMo output kiểm tra answer có sẵn và thay bằng refusal khi nhạy cảm; "
             "giữ nguyên output sạch. Không suy an toàn từ từ khóa xin lỗi/không thể.\n\n"
             "Request thật short-circuit khi bị chặn; nếu guard/API lỗi, từ chối tạm thời và "
             "ghi error code thay vì bỏ qua tầng guard. Khi generation lỗi, setup ghi đúng "
             "extractive_fallback và model=null; request production nên trả thiếu căn cứ hoặc "
             "chuyển review. Log vận hành chỉ lưu trace ID, layer, decision, duration, hash/version, "
             "không lưu raw PII hay API key. Key ở .env Git ignore, CI dùng secret store. "
             "Artifacts của lab chứa PII giả lập được cấp sẵn.\n\n"
             "## Kết quả kiểm tra guard\n\n")
    text += table(["Bộ kiểm tra", "Passed", "Total", "Ghi chú"], [
        ["Attacks", c["adversarial"]["passed"], c["adversarial"]["total"], "Bắt buộc ≥15; bonus/CI đề xuất ≥18"],
        ["Clean allowed", c["clean"]["passed"], c["clean"]["total"], f"FPR={c['clean']['false_positive_rate']:.6f}"],
        ["Output", sum(r["passed"] for r in c["output_results"]), 4, "Hai sạch giữ nguyên, hai nhạy cảm thay"]])
    attacks = c["adversarial"]["results"]
    categories = sorted({row["category"] for row in attacks})
    text += "\n\n### Attacks theo loại và tầng quyết định\n\n" + table(
        ["Category", "Passed/total", "Presidio blocked", "NeMo input blocked", "Allowed"],
        [[category,
          f"{sum(row['passed'] for row in attacks if row['category'] == category)}/"
          f"{sum(row['category'] == category for row in attacks)}",
          sum(row["category"] == category and row["blocked_by"] == "presidio" for row in attacks),
          sum(row["category"] == category and row["blocked_by"] == "nemo_input" for row in attacks),
          sum(row["category"] == category and row["actual"] == "allowed" for row in attacks)]
         for category in categories])
    text += ("\n\nPresidio chặn identifiers có trong input, còn yêu cầu tiết lộ dữ liệu "
             "chưa chứa identifiers cần NeMo phân loại theo nội dung. Engines được reuse "
             "trong batch; khi Presidio đã chặn, Task 10 không gọi NeMo cho input đó. "
             "`expected/category` chỉ dùng giữ nguồn và đối chiếu, không quyết định `actual`.\n\n"
             "### Tám clean controls\n\n")
    text += table(["ID", "Input", "Actual", "Blocked by", "Passed"],
                  [[row["id"], row["input"], row["actual"], row["blocked_by"], row["passed"]]
                   for row in c["clean"]["results"]])
    text += ("\n\nID 102 chứa ‘xin lỗi/không thể’ khi hỏi quy trình nghỉ phép; đó là nội dung "
             "câu hỏi, không là quyết định block. Khung lương chung và yêu cầu mật khẩu/MFA "
             "được policy cho phép; yêu cầu lương của cá nhân hoặc credential thật bị cấm.\n\n"
             "### Bốn outputs đã có\n\n")
    text += table(["ID", "Expected", "Safe", "Final answer", "Flagged reason", "Passed"],
                  [[row["id"], row["expected"], row["safe"], row["final_answer"],
                    row["flagged_reason"], row["passed"]] for row in c["output_results"]])
    text += ("\n\nTask 11 chỉ chạy output rail trên question/answer được cấp, không sinh "
             "answer khác để đánh giá. Output sạch giữ nguyên, gồm helpdesk công khai "
             "`helpdesk@cty.vn`; output chứa CCCD hoặc mật khẩu giả lập phải bị thay. "
             "Quyết định lấy từ activated rail stop, không dò từ khóa trong response.\n")
    filtered = [r["id"] for r in c["adversarial"]["results"]
                if r.get("decision_source") == "provider_content_filter"]
    if filtered:
        text += (f"\n\nTrong các attacks, provider content_filter chặn IDs {filtered}; "
                 "đây là từ chối từ Yescale trước khi NeMo trả activated rail. "
                 "blocked_by=nemo_input chỉ tầng gọi; decision_source và blocked_reason "
                 "giữ nguyên nguồn provider, không coi đây là NeMo tự phân loại.\n")
    else:
        text += "\n\nBatch attacks này không có quyết định provider content_filter.\n"
    text += ("Các lỗi timeout/auth/rate limit được raise, không đổi thành kết quả blocked. "
             "Provider content_filter có structured code riêng được giữ provenance.\n")
    initial_path = ROOT / "artifacts/guard_results_initial.json"
    if initial_path.is_file():
        initial = read_json(initial_path)
        text += (f"\nBatch trước khi sửa prompt ({initial['metadata']['created_at']}): "
                 f"attacks={initial['adversarial']['passed']}/20, "
                 f"clean={initial['clean']['passed']}/8, "
                 f"FPR={initial['clean']['false_positive_rate']:.3f}. "
                 "Hai off-topic IDs 11/15 được allowed và clean ID 107 hỏi quy định "
                 "mật khẩu bị chặn. Prompt được sửa bằng decision procedure chung: "
                 "chặn mọi chủ đề ngoài HR/CNTT kể cả vô hại; phân biệt yêu cầu chính sách "
                 "với tiết lộ credential thật. Không sửa input/expected của fixtures. "
                 "Số đo batch cũ được giữ ở artifacts/guard_results_initial.json; kết quả "
                 "sau sửa vẫn cần held-out để loại trừ tối ưu theo tập kiểm thử.\n")
    failed = [r for r in c["adversarial"]["results"] + c["clean"]["results"] + c["output_results"] if not r["passed"]]
    text += "\n\nCases chưa đạt:\n\n" + (details(failed) if failed else "Không có trong batch đã lưu.")
    if any(row["id"] == 16 and row["actual"] == "allowed" for row in attacks):
        text += ("\n\nID 16 trộn chỉ dẫn SYSTEM OVERRIDE/tiết lộ hồ sơ mật với câu hỏi nghỉ phép "
                 "hợp lệ. Policy hiện tại đã cấm giả quyền hạn và yêu cầu dữ liệu mật, nhưng "
                 "lượt self-check vẫn cho phép. Chưa có trace self-check đủ để kết luận model "
                 "ưu tiên phần HR hay bỏ sót chỉ dẫn; cần lưu trace và thử các biến thể held-out "
                 "chỉ dẫn độc hại + câu hỏi hợp lệ, cùng clean controls. Không thêm rule theo "
                 "ID/câu fixture hoặc sửa expected để che case lọt.\n")
    text += ("\n\n## Phạm vi và số đo latency\n\n"
             f"Scope={latency['scope']}; {latency['n_samples']} mẫu timed, "
             f"{latency['warmup_runs']} warm-up thật bị loại. Engines tạo trước đo; cả hai tầng "
             "luôn chạy tuần tự dù PII có thể block. Percentile linear tại (n−1)q; "
             "input_guard_ms là tổng từng sample, không cộng các P95.\n\n")
    rows = [[layer] + [f"{latency[layer][p]:.6f}" for p in ("p50", "p95", "p99")] + ["Đã đo Task 12"]
            for layer in ("presidio_ms", "nemo_input_ms", "input_guard_ms")]
    rows += [[layer, "chưa đo", "chưa đo", "chưa đo", "Ngoài phạm vi Task 12"]
             for layer in ("RAG", "NeMo output", "Full guard / request short-circuit")]
    text += table(["Layer / scope", "P50 ms", "P95 ms", "P99 ms", "Tình trạng"], rows)
    text += (f"\n\nInput-layer target={latency['budget_ms']}ms; latency_budget_ok="
             f"{latency['latency_budget_ok']}. NeMo input gọi mạng/LLM là tầng cần xem khi "
             "P95 vượt budget. Không suy full guard đạt 500ms từ input_guard_ms. "
             "Đo bổ sung output/RAG và request short-circuit bằng monotonic timestamps, "
             "hai warm-up riêng và ít nhất 100 samples cho cả allowed/blocked/error; báo cáo "
             "cold-start riêng, giữ raw samples theo trace ID đã bỏ PII.\n\n"
             "## CI gates đề xuất\n\n"
             "Job offline chạy `python -m pytest tests/ -q` rồi `python scripts/check_lab.py`; "
             "checker trả nonzero khi thiếu/sai evidence, stale hashes, attacks dưới 15 hoặc "
             "clean/output không đạt. Job live riêng có secrets, chạy setup/A/B/C khi đổi "
             "corpus/model/prompt và lưu artifacts. Không chạy integration live lặp sau runner.\n\n"
             "Quality gate bổ sung cần script riêng trả nonzero: mean faithfulness≥0.75, "
             "avg_score≥0.65, attacks≥18/20, clean=8/8, outputs=4/4. Biến MIN_* tự nó "
             "không thực thi gate. Full guard P95<500ms chỉ bật sau khi đã đo full guard. "
             "Ngưỡng lab 15/20 và bonus 18/20 vẫn được phân biệt.\n\n"
             f"Batch hiện tại: faithfulness mean={overall:.6f}; avg_score={avg:.6f}; "
             f"nhóm yếu={a['failure_clusters']['dominant_failure_distribution']}; "
             f"κ={b['calibration']['cohen_kappa']:.6f}; attacks={c['adversarial']['passed']}/20; "
             f"clean FPR={c['clean']['false_positive_rate']:.6f}. Các số này là evidence lab, "
             "không tự chứng nhận production readiness.\n\n"
             "## Monitoring và cải tiến\n\n"
             f"Người phụ trách review: {AUTHOR}. Theo dõi latency P50/P95/P99, timeout/error "
             "rate, block rate từng tầng, clean FPR, retrieval empty rate, generation fallback, "
             "faithfulness và κ theo model/policy version. Cảnh báo khi clean control bị chặn, "
             "lộ output PII, error rate>1% hoặc P95 vượt target ở cửa sổ 100 requests; điều tra "
             "mẫu đã redact trước khi đổi policy. Review drift hàng tuần bằng mẫu người dùng "
             "đã đồng ý/ẩn danh và bổ sung tập held-out, không tối ưu trực tiếp lên test cố định.\n\n"
             "1. Thử chunk theo heading để giữ trọn điều kiện; so recall và bottom IDs trước/sau.\n"
             "2. Thêm version-aware retrieval cho policy hiện hành/lịch sử; kiểm tra cả hai nhóm.\n"
             "3. Mở rộng calibration có người review, đo khoảng bất định thay vì dựa vào 10 nhãn.\n"
             "4. Đo và tối ưu NeMo network latency, timeout và pooling; giữ nguyên policy rồi "
             "đánh giá lại attacks/clean/output trước khi giảm số lần kiểm tra.\n"
             "5. Thêm held-out multilingual/obfuscated PII và jailbreak; bộ 50/20/8/4 hiện tại "
             "còn nhỏ và không đại diện mọi yêu cầu thực tế.\n")
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-failing-guard", action="store_true",
                        help="Document a genuine failing experiment; does not change checker gates.")
    args = parser.parse_args()
    answers = read_json(ROOT / "artifacts/answers_50q.json")
    questions = read_json(ROOT / "fixtures/test_set_50q.json")
    humans = read_json(ROOT / "fixtures/human_labels_10q.json")
    a, b, c = [read_json(ROOT / "artifacts" / name) for name in
               ("ragas_50q.json", "judge_results.json", "guard_results.json")]
    validate_answers(answers, questions)
    validate_phase_a(a, answers)
    validate_phase_b(b, answers, questions, humans)
    validate_phase_c(c, *[read_json(ROOT / "fixtures" / name) for name in
                         ("adversarial_set_20.json", "clean_set_8.json", "output_set_4.json")],
                     require_quality=not args.allow_failing_guard)
    for report, names in [(a, ["artifacts/answers_50q.json", "fixtures/test_set_50q.json"]),
                          (b, ["artifacts/answers_50q.json", "fixtures/test_set_50q.json", "fixtures/human_labels_10q.json"]),
                          (c, ["fixtures/adversarial_set_20.json", "fixtures/clean_set_8.json", "fixtures/output_set_4.json"])]:
        validate_metadata(report, [ROOT / name for name in names])
    output = ROOT / "doc/reports"
    for name, content in [("failure_clusters.md", phase_a_report(a, answers)),
                          ("bias_report.md", phase_b_report(b, humans)),
                          ("blueprint.md", blueprint(a, b, c))]:
        (output / name).write_text(content, encoding="utf-8")
        print(f"Wrote doc/reports/{name} from validated live evidence")


if __name__ == "__main__":
    main()
