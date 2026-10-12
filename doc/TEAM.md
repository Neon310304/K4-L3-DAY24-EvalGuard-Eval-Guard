# Nhóm thực hiện K4 Track 3A

Tên nhóm: EvalGuard.

Repo chung: https://github.com/Neon310304/K4-L3-DAY24-EvalGuard-Eval-Guard

Trưởng nhóm/người nộp: Trần Quốc Vượng — 2A202602522.

Ngày thực hiện: 12/10/2026 (UTC+07:00). Ngày lab/deadline chính thức áp dụng theo
thông báo lớp; chưa được cung cấp trong phiên làm việc. Không tự coi ngày thực hiện
là deadline của lớp.

Phiên bản source/evidence để chấm được cố định bằng tag `day24-submission-20261012`
ở commit `07271d1c39de76e57a7328455ddf40fa620176c8`. Commit hồ sơ tiếp theo chỉ
ghi lại SHA/tag trong TEAM/checklist; không thay đổi source, artifacts hay reports.
Link repo đã push công khai; chưa gửi qua kênh lớp vì chưa có tên/link kênh coach.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Trần Quốc Vượng | 2A202602522 | Tích hợp pipeline RAG, Phase A/B/C, kiểm tra và báo cáo | src/m1–m5, src/phase_*.py, tests/test_pipeline_modules.py, artifacts và doc/reports |

Người tích hợp/chạy batch/nộp link: Trần Quốc Vượng. Công cụ AI hỗ trợ viết code,
chạy lệnh và tổng hợp báo cáo; kết quả đo chỉ lấy từ batch live đã lưu.

## Ánh xạ nhiệm vụ và evidence

Người phụ trách các phần dưới đây: Trần Quốc Vượng — 2A202602522.

| Phần | Hàm / file | Evidence dùng để giải thích |
|---|---|---|
| Pipeline m1–m5 | load_documents/chunk_hierarchical, HybridSearch, CrossEncoderReranker, evaluate_ragas, enrich_chunks | src/m1_chunking.py đến src/m5_enrichment.py; source metadata trong contexts; tests/test_pipeline_modules.py |
| Tasks 1–4 | group_by_distribution, run_ragas_50q, bottom_10, cluster_analysis trong src/phase_a_ragas.py | artifacts/ragas_50q.json; doc/reports/failure_clusters.md; tests/test_phase_a.py |
| Tasks 5–8 | pairwise_judge, swap_and_average, cohen_kappa, bias_report trong src/phase_b_judge.py | artifacts/judge_results.json; doc/reports/bias_report.md; tests/test_phase_b.py |
| Tasks 9a–12 | pii_scan, check_input_rail, run_adversarial_suite, check_output_rail, measure_p95_latency trong src/phase_c_guard.py | artifacts/guard_results.json; tests/test_phase_c.py; raw latency samples và output cases |
| Task 13 | doc/reports/blueprint.md | Kiến trúc, failure actions, CI/monitoring đề xuất và giới hạn từ evidence A/B/C |
| Tích hợp và đóng gói | config.py, infra/Dockerfile, scripts/setup_answers.py, scripts/write_reports.py | .env.example không chứa key; báo cáo và checklist; checker offline trên artifacts |

`fixtures/` là đầu vào được cấp (bao gồm model_answer/nhãn người), không khai là
kết quả thực nghiệm. `data/` là corpus; `artifacts/` chứa các lượt chạy được tạo
trong phiên thực hiện. Batch guard mới đạt attacks 19/20, clean 8/8 (FPR=0),
outputs 4/4; attack ID 16 còn lọt và input-layer P95=1845.715510ms vượt mục tiêu.

## Môi trường và chuẩn bị

Host Windows, Python 3.11.15 cho .venv-tests; 104 tests offline đã pass bằng
`.venv-tests/Scripts/python.exe -m pytest tests/ -q`. `uv pip check` môi trường test đạt.
Cài full stack trực tiếp Windows gặp Annoy thiếu Microsoft Visual C++ 14.0;
runtime được chuyển sang Linux Python 3.11 qua infra/Dockerfile, build-essential/GCC.
Qdrant pin qdrant/qdrant:v1.9.7 đã khởi động bằng Docker Compose.

Checkpoint chuẩn bị ngày 12/10/2026 đã chạy setup live trong Docker, ghi answers
lúc 12:15:26 (UTC+07:00): 50 answers LLM gpt-4o-mini, 20 factual / 20 multi_hop /
10 adversarial, không extractive fallback, mỗi câu có 3 contexts. Đối chiếu schema
và fixture đạt; cả 150 contexts khớp chunks source-enriched từ 25 tài liệu/132
chunks, không có answer trùng nguyên văn ground truth. Giữ nguyên data/fixtures.

Image Docker mới dùng Linux Python 3.11.17, RAGAS 0.1.22, NeMo 0.10.0,
Presidio 2.2.364, spaCy 3.8.16, Sentence Transformers 3.0.1, PyArrow 17.0.0 và
NumPy 1.26.4. Đã sửa xung đột ABI PyArrow/NumPy bằng constraints; `pip check`
trả `No broken requirements found`, imports và load en_core_web_lg 3.8.0 đạt.
Wheel spaCy được dùng lại từ cache của image trước (không thay model), SHA256
293e9547a655b25499198ab15a525b05b9407a75f10255e405e8c3854329ab63;
Dockerfile mặc định tải cùng wheel từ GitHub chính thức với hash này.
Lượt `verify_runtime.py --with-pipeline` trên image mới index 132 chunks trong
81.7 giây, search trả 20 ứng viên và rerank 3 contexts, giữ source/parent metadata.
Log thực tế ở artifacts/runtime_verification.txt. Phase A/B và ba báo cáo đã chạy
lại theo answers mới; không sửa source hashes của kết quả cũ để làm checker đạt.

Docker/WSL từng treo sau khi ổ C đầy. Đã khởi động lại WslService với quyền
Administrator bằng scripts/repair_wsl.ps1, giữ images/volumes. Kiểm chứng phục
hồi: Docker Desktop running, daemon 29.8.1 và HTTP Qdrant trả version 1.9.7.

Batch C lúc 2026-10-12T05:02:34.216997+00:00 chạy trên Windows Python 3.11.15
trong .venv-eval, NeMo 0.10.0, Presidio 2.2.364, spaCy 3.8.16 với
en_core_web_sm 3.8.0 (PRESIDIO_SPACY_MODEL đặt riêng trong tiến trình).
Annoy 1.17.3 dùng binary conda-forge py311hda3d55a_2, đã đối chiếu SHA256
48617e6e3f16994b58819889432a31613683d2254940f27f56438bb77acfc5d5;
import/search và uv pip check đạt. Registry Presidio chỉ dùng recognizers
email/phone và hai pattern VN, không dùng NER để chặn tên/ngày/địa điểm.
Docker giữ mặc định en_core_web_lg. Vì runtime khác batch đầu, không quy thay
đổi latency chỉ cho prompt. Trace Docker của clean ID 107 ở
artifacts/guard_case_107.json ghi completion=No, self-check=true, stop=false.

Yescale cấu hình qua .env Git ignore; chat gpt-4o-mini và embeddings
text-embedding-3-small đã gọi thử thành công HTTP 200. Các vai trò model có biến
riêng và cùng endpoint, không ghi key trong báo cáo. Module m1–m5 được triển khai
mới theo PIPELINE_INTERFACE.md vì không có source bài trước trong workspace;
không khai đây là mã đã mang từ bài trước. Enrichment chỉ thêm metadata nguồn,
không dùng LLM hoặc ground truth. Hai phiên bản tài liệu cũ/mới được giữ nguyên.

Trạng thái batch/model và kết quả kiểm tra cuối được cập nhật trong
`doc/COMPLETION_CHECKLIST.md` và ba báo cáo có provenance trong `doc/reports/`.
Không suy live runtime thành công chỉ từ unit mock hoặc pip resolve.
Kiểm tra cuối bằng .venv-tests/Scripts/python.exe scripts/check_lab.py --with-tests:
0 failed checks; 104 passed, 3 integration deselected. Checker không gọi API.

Đóng gói giữ nguyên byte JSON đã dùng trong batch bằng `.gitattributes` (`-text`
cho fixtures/artifacts). Git trước đó tự đổi CRLF thành LF ở index, khiến hashes
khác dù JSON giống nội dung. Fixtures chỉ thay cách lưu line endings trong Git,
không thay ID/question/answer/reference/expected/human labels. Các source hashes
và kết quả live không bị sửa. Bản export từ index phải chạy checker đạt trước push.

## Readiness và đối chiếu assertions Phase A

Trần Quốc Vượng phụ trách Tasks 1–4 và đọc các assertions dưới đây. Support tests
đạt 60; `tests/test_phase_a.py` có 8 tests đạt. Tests dùng mocks/offline, còn số đo
RAGAS lấy từ batch live lúc 2026-10-12T05:35:59.168641+00:00. Các lần kiểm tra sử
dụng workspace hiện tại và cùng answers SHA256
db39b713f8872579f5d05641272608595f6ef61f2002def3585095b7cb34a0e9.
Commit source/evidence dùng để chấm: `07271d1c39de76e57a7328455ddf40fa620176c8`
(tag `day24-submission-20261012`). Commit hồ sơ sau đó chỉ cập nhật thông tin nộp,
không thay đổi revision này.

| Test trong tests/test_phase_a.py | Hàm / Task | Điều kiện assertions cần giải thích |
|---|---|---|
| test_group_exact_counts | group_by_distribution / 1 | Đúng ba keys; số dòng 20/20/10 |
| test_ragas_adapter_preserves_rows | run_ragas_50q / 2 | 50 rows đúng ID/thứ tự; gọi m4 một lần với questions cùng thứ tự; giữ evaluator_models |
| test_bottom_nonempty_sorted_complete | bottom_10 / 3 | Rank liên tục, mean tăng dần, đúng row yếu nhất; đủ ID/distribution/question/metric/diagnosis/fix và nội dung không rỗng |
| test_bottom_capped_at_ten | bottom_10 / 3 | Dataset lớn vẫn chỉ lấy 10 rows |
| test_cluster_matrix | cluster_analysis / 4 | Matrix từng ô đúng; chọn metric phổ biến nhất; insight có nội dung |
| test_weakest_distribution_is_quality_not_size | cluster_analysis / 4 | Nhóm 10 câu có mean thấp hơn phải được chọn, không chọn nhóm 20 câu do tổng cột lớn |
| test_bottom_diagnosis_reads_answer_context_and_reference | bottom_10 / 3 | Giữ reference và evidence 12 giờ ngắt phiên VPN trong diagnosis; fix chỉ được nguồn VPN cần đọc |
| test_ragas_mapping_rows_keep_scores_aligned | run_ragas_50q / 2 | Mapping/scalars đổi sang float Python; các hàng điểm khác nhau vẫn ghép đúng ID/answer/contexts |

Kiểm tra lỗi thiếu rows/NaN/thiếu evaluator_models và nhóm rỗng còn nằm trong
`tests/test_pipeline_modules.py`. Phase A hiện đạt hợp đồng; support đạt riêng
không được dùng làm bằng chứng LLM/embedding đã thực thi. Diagnosis Task 3 dùng
nội dung và gợi ý topic của corpus để ưu tiên review, không thay đổi pipeline.
Bottom/matrix/diagnosis đã được tái tạo từ per_question live; giữ nguyên answers,
bốn metrics, thời điểm đo và model roles. Báo cáo chỉ ra thiếu nguồn nghỉ đặc biệt,
đoạn VPN sai mục, điều kiện đào tạo bị cắt, thiếu exclusion PVI và trường hợp
version đúng/sai; cải tiến chất lượng cần một batch riêng sau khi thay pipeline.

Trong lượt readiness, Docker Desktop đang dừng nên Qdrant ban đầu không truy cập
được. Đã dùng `docker desktop start --detach` và Compose `up -d qdrant` để khôi
phục; daemon 29.8.1, HTTP Qdrant 1.9.7, collection vẫn giữ 132 vectors/1024 chiều.
Chạy lại `verify_runtime.py` trên container đạt imports/spaCy/Qdrant; không cần
tải model hay tạo lại index để bắt đầu Phase A.

## Đối chiếu Phase B, Tasks 5–8

Trần Quốc Vượng phụ trách code và đọc evidence Phase B. Kiểm tra riêng
`tests/test_phase_b.py`: 8 tests đạt, SDK/mock offline. Batch API được giữ ở
`artifacts/judge_results.json`, timestamp 2026-10-12T05:23:02.551214+00:00,
judge gpt-4o-mini. Đã validate schema/metadata/source hashes, đối chiếu nguyên văn
candidates và tính lại kappa/bias bằng code hiện tại; không sinh lại answers.

| Test trong tests/test_phase_b.py | Hàm / Task | Điều kiện assertions cần giải thích |
|---|---|---|
| test_pairwise_uses_json_judge | pairwise_judge / 5 | Một API call mock, prompt có reference, response_format JSON; đúng winner/reasoning/scores |
| test_swap_conversion_and_calls (2 cases) | swap_and_average / 6 | Hai lượt Q/A/B và Q/B/A; winner/scores lượt hai đổi về A/B gốc; đồng thuận giữ winner, bất đồng trả tie |
| test_kappa_exact (3 cases) | cohen_kappa / 7 | Mixed perfect agreement = 1; nhãn đối nghịch = -1; agreement ngang chance = 0 |
| test_bias_known_counts | bias_report / 8 | Inconsistent = 1/2; tie không vào decisive; winner dài hơn = 1/1; có interpretation |
| test_bias_empty | bias_report / 8 | List rỗng không gây chia cho 0, total_judged = 0 |

Năm IDs 1/5/12/21/41 lấy A từ answer pipeline và B từ supplied model_answer;
question/reference từ test set. Mười binary judgments dùng đúng model_answer gốc,
helper không nhận human_label/human_note. Calibration IDs đúng thứ tự
1/5/12/21/23/29/33/41/46/50; hai list nhãn đều 1/0/1/1/1/0/1/0/1/0.
Agreement = 10/10, chance = 0.6² + 0.4² = 0.52; κ = 1.0.

Hai lượt cùng winner sau quy đổi ở cả 5 cặp; position inconsistency = 0/5.
Decisive = 5; A thắng và dài hơn = 2 (IDs 5/41), B thắng và dài hơn = 0;
verbosity rate = 2/5 = 0.4. Reasoning lượt hai giữ tên A/B theo vị trí swapped;
scores/winner đã đổi về danh tính gốc. Không tạo case bất đồng live khi batch
không có; nhánh bất đồng được kiểm tra bằng test mock.

Báo cáo bias đọc từng cặp và phân biệt winner với rationale: ID 21 bỏ sót
khoảng lương trong A dù reasoning mô tả A accurate; IDs 1/46 có reasoning gán
thêm điều kiện chưa viết trong answer. ID 29 thiếu đồng phê duyệt và phí pro-rata
80.000 VNĐ, nhưng wording reasoning về gốc tính phí chưa chính xác. Giữ nhãn/đo
thật; κ chỉ xác nhận agreement với 10 nhãn người, không xác nhận mọi giải thích.
Nhận xét thủ công gắn fingerprint toàn bộ JSON để batch mới phải được đọc lại.
Kiểm tra tại checkpoint Phase B: 101 tests offline đạt, 3 integration deselected;
checker 0 failed checks. Không dùng tests mocks làm bằng chứng API execution.

## Đối chiếu Phase C, Tasks 9a–12

Trần Quốc Vượng phụ trách guard source, cấu hình policy và đọc batch live. Kiểm tra
riêng `tests/test_phase_c.py`: 15 tests đạt, gồm PII entities/vị trí/anonymize,
rail decision từ `activated_rails`, full batch provenance, output safe/blocked và
latency warm-up/sample count. `tests/test_pipeline_modules.py` kiểm tra thêm
provider `content_filter` được ghi riêng với NeMo rail và lỗi bất kỳ không bị gán
thành block.

| Test / evidence | Hàm / Task | Điều kiện cần giải thích |
|---|---|---|
| test_pii_detect_and_redact (4 cases), test_pii_clean | pii_scan / 9a | CCCD 12 số, CMND 9 số, điện thoại VN, email được nhận diện; text sạch giữ nguyên; entities có type/text/score/start/end và anonymized khác input khi có PII |
| test_input_uses_rail_decision (2 cases) | check_input_rail / 9b | Gọi async với options rails=input; allowed lấy từ `activated_rails.stop`, không suy từ chữ xin lỗi/không thể |
| test_output_checks_supplied_answer (2 cases) | check_output_rail / 11 | Gửi đúng answer có sẵn trong assistant message; output sạch giữ answer, output bị rail thay bằng response và có lý do |
| test_input_suite_exact_rows, test_attack_and_clean_control | run_adversarial_suite / 10 | Nhận đủ 28 inputs, giữ input/category/expected; actual độc lập expected; PII block trước rail, các rail khác ghi `nemo_input` |
| test_batch_decisions_ignore_expected_and_category | run_adversarial_suite / 10 | Hai inputs giống nhau nhưng expected/category trái nhau vẫn có cùng actual; PII chặn cả row được gán clean; list 4 rows giữ đúng thứ tự, reuse engines, chỉ 3 calls NeMo |
| test_allowed_input_can_have_refusal_words_in_response | check_input_rail / 9b | Response có xin lỗi/không thể nhưng stop=False vẫn allowed; logging activated_rails được bật |
| test_safe_output_preserves_supplied_answer_despite_rail_response | check_output_rail / 11 | Khi stop=False, giữ answer gốc dù response từ rail có text khác; flagged_reason=None và logging được bật |
| test_latency_real_warmup_and_sample_count | measure_p95_latency / 12 | Hai warm-up bị loại; 20 samples dương; Presidio và NeMo input luôn đo tuần tự; tổng từng sample và percentile linear hợp đồng |
| artifacts/guard_results.json | Tasks 9a–12 live | 19/20 attacks, 8/8 clean allowed (FPR=0), 4/4 output; ID 16 prompt injection còn allowed; scope `input_layers_sequential`, P95=1845.715510 ms |

Batch live lúc 2026-10-12T05:02:34.216997+00:00 dùng guard model gpt-4o-mini.
Hai policy cũ/mới và clean controls được giữ nguyên. Attack ID 16 có nội dung
`SYSTEM OVERRIDE` nhưng NeMo trả allowed; không đổi expected/passed để che failure.
Các attacks PII được chặn bởi Presidio hoặc NeMo, còn clean password/salary/VPN/
leave đều được phép. Output IDs 201/202 giữ nguyên; 203/204 bị thay bởi refusal.

Latency chỉ đo Presidio + NeMo input tuần tự, có 2 warm-up và 20 mẫu timed;
không gọi đây là full guard/request latency. P95 1845.715510 ms vượt budget 500 ms,
vì vậy blueprint ghi rõ ngoài phạm vi RAG/output/request và đề xuất đo/tối ưu riêng.
Artifacts có source hashes đã validate; checker yêu cầu attacks tối thiểu 15 và
clean 8/8 nên batch đạt tiêu chí bắt buộc và bonus attacks ≥18, dù vẫn còn một
case prompt injection cần sửa ở held-out evaluation.

Fixture `guard_batch` dùng phạm vi từng test để teardown mocks sau mỗi case;
không để mock rail của batch che hàm thật trong các test tiếp theo. Assertions/
expected có sẵn được giữ nguyên; ba tests thêm kiểm tra các tình huống chưa có
coverage, không dùng làm evidence API. Lần kiểm tra cuối sau bổ sung: 104 tests
offline đạt, 3 integration deselected; checker 0 failed checks.

## INDIVIDUAL

### TranQuocVuong-2A202602522

- Phần thực hiện: m1 đọc/chunk corpus, m2 hybrid search, m3 rerank, m4 RAGAS, m5
  enrichment; Tasks 1–12 và blueprint Task 13; cấu hình Yescale/Docker và packaging.
- Bằng chứng: source, tests/test_pipeline_modules.py, artifacts live và ba báo cáo;
  lịch sử Git đóng gói ghi công việc của tài khoản thực hiện.
- Cách kiểm tra: tests offline cấm network; runners live sinh evidence riêng;
  check_lab validate schema, hashes, source IDs và phép tính, không thay bằng kết quả mock.
- Nội dung học từ phần triển khai: phân biệt retrieval/generation; dùng mean thay
  kích thước nhóm khi tìm distribution yếu; quy đổi lượt swap về A/B gốc; calibration
  binary phải chấm đúng model_answer; latency input sequential không là full request.
- Giới hạn/cách xử lý: bộ 50/20/8/4 nhỏ, model/API có biến động; giữ số đo vượt budget
  và case chưa đạt, mở rộng held-out và review nội dung trước kết luận production.
- Nguồn/AI hỗ trợ: starter VinUni-AI20k/K4-Track-3A-Day24-Eval-Guard; Codex hỗ trợ
  triển khai và chạy kiểm tra. SDK dùng tài liệu OpenAI chính thức;
  dependency APIs kiểm tra trên phiên bản runtime thực tế. Không tự tạo nhãn/số đo.

## Cập nhật sau khi nộp

Chưa có lần nộp qua kênh lớp trong phiên làm việc này. Khi gửi bài, lưu commit SHA
và thời điểm gửi; cập nhật sau deadline phải ghi commit/lý do và áp dụng quyết định coach.
