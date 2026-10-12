# Checklist thực hiện bài lab

## Checkpoint 1 — Mở starter và xác định bài nộp

- [x] Mở đúng workspace tại gốc repo có `README.md` và `src/`.
- [x] Xác định starter: https://github.com/VinUni-AI20k/K4-Track-3A-Day24-Eval-Guard.
- [x] Repo chung công khai, đúng mẫu tên: https://github.com/Neon310304/K4-L3-DAY24-EvalGuard-Eval-Guard.
- [x] Đối chiếu ASSIGNMENT/RUBRIC với các hàm Tasks 1–12 và blueprint Task 13.
- [x] Điền Trần Quốc Vượng — 2A202602522; người tích hợp/chạy batch/người nộp trong TEAM.
- [x] Có mục INDIVIDUAL và bảng ánh xạ nhiệm vụ → hàm/file → evidence trong TEAM.
- [x] Phân biệt fixtures được cấp, corpus data và artifacts do các runner tạo ra.

## Checkpoint 2 — Chuẩn bị pipeline và sinh 50 answers

- [x] Có đủ m1–m5 với giao diện theo `doc/PIPELINE_INTERFACE.md`; setup tự lắp
  m1/m2/m3/m5, Phase A gọi m4.
- [x] Qdrant v1.9.7 hoạt động; collection `lab24_production` chứa 132 vectors
  có 1024 chiều, từ 25 tài liệu trong corpus.
- [x] BGE-M3 và FlashRank đã tải, indexing/reranking đã chạy trong lượt setup live.
- [x] Chạy `docker compose -f infra/docker-compose.yml run --rm lab python scripts/setup_answers.py --live`;
  file answers mới được ghi lúc 12:15:26 ngày 12/10/2026 (UTC+07:00).
- [x] Validate JSON Schema Answers và đối chiếu fixture: đúng 50 IDs cùng
  question/distribution/ground_truth, phân bố 20 factual / 20 multi_hop / 10 adversarial.
- [x] Có 50 `generation_mode=llm`, model `gpt-4o-mini`; không có extractive fallback.
  Mỗi answer có 3 contexts; không có answer trùng nguyên văn ground truth.
- [x] Đối chiếu cả 150 contexts: khớp chính xác chunks qua source enrichment;
  vẫn giữ policy nghỉ phép 2023/2024 và mật khẩu v1/v2, không sửa `data/`/`fixtures/`.
- [x] `.env` có cấu hình Yescale và được Git ignore; không đưa key vào source/evidence.
- [x] Hoàn tất rebuild Docker: Python 3.11.17, PyArrow 17.0.0/NumPy 1.26.4;
  `pip check` đạt, imports full runtime và load `en_core_web_lg` 3.8.0 thành công.
  `verify_runtime.py --with-pipeline` chạy indexing/search/rerank thực tế;
  xem `artifacts/runtime_verification.txt`.
- [x] Đồng bộ lại Phase A/B và báo cáo theo answers mới; giữ kết quả guard độc lập.
  Checker trên artifacts mới đạt `0 failed checks`.

SHA256 answers của lượt setup mới:
`db39b713f8872579f5d05641272608595f6ef61f2002def3585095b7cb34a0e9`.

## Checkpoint 3 — Kiểm tra sẵn sàng đầu buổi

- [x] Phân biệt `.venv-tests` Python 3.11 cho tests offline và full runtime Linux
  Docker Python 3.11.17; imports/model/Qdrant đã chạy thật ở checkpoint trước.
- [x] `python -m pytest tests/ -m support -q`: 60 support tests đạt.
- [x] Đọc tests Phase A và nối assertions với Tasks 1–4 trong TEAM.
- [x] Không còn TODO gây student test fail; các mẫu báo cáo đã có evidence thật.
  Support tests chỉ kiểm tra scaffold, không thay các batch live.
- [x] Dùng cùng answers SHA256 ở checkpoint 2; không sinh lại answers trong Phase A.
  Không còn download/indexing lớn phải chờ để bắt đầu phase này.
- [x] Lượt kiểm tra readiness phát hiện Docker Desktop đang dừng; đã khởi động lại
  Docker và Qdrant. HTTP Qdrant v1.9.7, collection vẫn giữ 132 vectors/1024 chiều;
  `verify_runtime.py` sau restart đạt imports, spaCy model và kết nối Qdrant.

## Checkpoint 4 — Phase A, Tasks 1–4

- [x] Task 1: factual/multi_hop/adversarial đúng 20/20/10, giữ ID và nội dung.
- [x] Task 2: 50 results đúng thứ tự, 4 floats hữu hạn [0,1], nhận cả mapping rows;
  evaluator model IDs lấy từ m4: gpt-4o-mini và text-embedding-3-small.
- [x] Task 3: 10 bottom rows tăng dần mean, rank/diagnosis/fix đầy đủ; phân tích
  answer/context/reference và nguồn còn thiếu, không quy nguyên nhân chỉ từ metric.
- [x] Task 4: matrix đếm mỗi câu một lần; tổng cột 20/20/10; nhóm yếu theo mean
  là multi_hop 0.516140 (factual 0.558209, adversarial 0.540863).
- [x] Batch RAGAS live gốc: 2026-10-12T05:35:59.168641+00:00. Cập nhật bottom,
  matrix và diagnosis từ metrics đã lưu, giữ metadata/điểm/answers nguyên nguồn.
- [x] `tests/test_phase_a.py`: 8 tests đạt, bao gồm mapping/order và đọc evidence.
- [x] Báo cáo có bảng bốn metrics/câu, contexts, nhận xét từng bottom row, phân
  tích bẫy phiên bản/phủ định và thứ tự cải tiến; qualitative review gắn answers hash.
- [x] Tại checkpoint Phase A, checker đạt 0 failed checks; 101 tests offline đạt,
  3 integration deselected. Lần mới nhất xem bảng trạng thái tổng hợp.

## Checkpoint 5 — Phase B, Tasks 5–8

- [x] Task 5: pairwise dùng reference, trả winner A/B/tie, reasoning có nội dung,
  scores A/B hữu hạn [0,1]; giữ nội dung API trả về.
- [x] Task 6: hai lượt/cặp với cùng question/reference, đổi winner/scores lượt hai
  về A/B gốc; đồng thuận giữ winner, bất đồng thành tie. Reasoning lượt hai giữ
  nguyên tên theo vị trí swapped và được giải thích trong báo cáo.
- [x] Năm cặp IDs 1/5/12/21/41: A đúng answer pipeline, B đúng supplied
  model_answer, reference đúng test set; pair_sources và source hashes đã validate.
- [x] Có 10 binary judgments trên đúng question/model_answer gốc ở human fixture;
  không gửi human_label/human_note vào prompt, không chuyển winner A/B sang 0/1.
- [x] Task 7: calibration aligned IDs/thứ tự; judge=human ở cả 10 câu, 6 nhãn 1
  và 4 nhãn 0; p_o=1, p_e=0.52, κ=1.0. Giữ kết quả thật của batch.
- [x] Task 8: position inconsistency 0/5; decisive=5, A thắng và dài hơn=2,
  B thắng và dài hơn=0; verbosity rate=0.4. Counts được tính lại bằng source hiện tại.
- [x] Batch live 2026-10-12T05:23:02.551214+00:00, judge gpt-4o-mini;
  answers SHA256 vẫn giữ từ checkpoint 2, không đổi inputs giữa các phase.
- [x] `tests/test_phase_b.py`: 8 tests đạt; ánh xạ assertions Tasks 5–8 trong TEAM.
  Tại checkpoint Phase B có 101 tests offline đạt, 3 integration deselected;
  checker 0 failed checks. Lần mới nhất xem bảng trạng thái tổng hợp.
- [x] Bias report có sources, hai lượt, nhãn/ma trận κ, counts và review 5 cặp;
  chỉ ra reasoning lệch ở IDs 1/21/29/46, giới hạn mẫu nhỏ và raw-vs-mapped A/B.
  Nhận xét thủ công gắn fingerprint toàn bộ batch để tránh tái dùng cho lần chạy khác.

## Checkpoint 6 — Phase C, Tasks 9a–12

- [x] Task 9a: `pii_scan` dùng Presidio, trả `has_pii`, entity type/text/score/vị trí
  và anonymized text; kiểm tra CCCD/CMND, điện thoại Việt Nam, email và clean input.
- [x] Task 9b: `check_input_rail` async truyền đúng input rails + logging options,
  đọc `activated_rails.stop`/response; không quyết định bằng heuristic từ khóa refusal.
- [x] Task 10: `run_adversarial_suite` nhận batch 28 inputs, giữ nguyên fixture fields,
  quyết định actual trước khi so expected, ghi `blocked_by`, `decision_source` và lý do.
- [x] Task 11: `check_output_rail` async gửi answer đã có; safe giữ nguyên answer,
  blocked thay/redact và giữ flagged reason. Live outputs đạt 4/4.
- [x] Task 12: tạo engines trước đo, 2 warm-up thật, 20 samples timed dương,
  scope=`input_layers_sequential`, percentile linear và `input_guard_ms` là tổng
  từng sample; không gọi đây là full guard latency.
- [x] Batch live 2026-10-12T05:02:34.216997+00:00: attacks 19/20 (bonus ≥18),
  clean 8/8 allowed, FPR=0, outputs 4/4. Attack ID 16 còn lọt và được giữ nguyên
  trong artifact/report để phân tích; không sửa expected hoặc passed.
- [x] Latency live: 20 samples, 2 warm-up; Presidio P95=16.536615 ms,
  NeMo input P95=1838.980410 ms, input sequential P95=1845.715510 ms, vượt
  budget 500 ms. RAG/output/full request ghi ngoài phạm vi.
- [x] `tests/test_phase_c.py`: 15 tests đạt; thêm cases expected/category độc lập
  actual, response có từ chối nhưng allowed, safe output giữ answer dù rail response
  khác. Fixture mocks được teardown mỗi test; giữ nguyên assertions/expected cũ.
  Pipeline failure-path tests kiểm tra
  provider content_filter riêng và arbitrary errors không bị đổi thành blocked.
- [x] Blueprint ghi kiến trúc, failure action, clean/attack/output evidence, case
  ID 16, latency scope/budget và kế hoạch held-out/monitoring; checker 0 lỗi.
- [x] Kiểm tra cuối sau bổ sung tests: 104 passed, 3 integration deselected;
  `check_lab.py --with-tests` trả 0 failed checks, `git diff --check` đạt.

## Trạng thái tổng hợp

| Hạng mục | Trạng thái | Bằng chứng / giới hạn |
|---|---|---|
| Python 3.11 cho tests | Đạt | .venv-tests; uv pip check đã pass |
| Full runtime Docker Python 3.11.17 | Đạt | pip check/imports, en_core_web_lg 3.8.0, 132 chunks indexed; 20 candidates → 3 reranked contexts; metadata được giữ |
| Unit tests offline | Đạt ở lần chạy gần nhất | 104 passed, 3 integration deselected; không thay thế live experiments |
| Yescale | Đã cấu hình và gọi thử | Chat/embeddings HTTP 200; .env được Git ignore |
| Qdrant v1.9.7 | Đang chạy | Docker/WSL đã phục hồi; daemon 29.8.1, Qdrant HTTP trả version 1.9.7 |
| m1–m5 | Có đủ source | Triển khai mới theo PIPELINE_INTERFACE; giữ policy cũ/mới và provenance |
| Phase A, Tasks 1–4 | Source và evidence đạt hợp đồng | 50 per_question, 10 bottom rows, matrix/means; artifacts/ragas_50q.json đã validate |
| Phase B, Tasks 5–8 | Source và evidence đạt hợp đồng | 5 cặp, 10 binary judgments đúng model_answer nguồn; κ=1.0 |
| Phase C, Tasks 9a–12 | Source và evidence đạt hợp đồng | Batch mới: attacks 19/20, clean 8/8, outputs 4/4; còn lọt attack ID 16 |
| 50 answers | Đủ và đã validate | 50 LLM answers; factual/multi_hop/adversarial=20/20/10; không fallback |
| Bốn JSON bắt buộc | Có đủ và đã validate | Answers/A/B/C đạt schema, nguồn và phép tính; không sửa số đo để ép đạt |
| Ba báo cáo | Đã cập nhật từ evidence | Ghi lỗi RAG, giới hạn judge, attack còn lọt và input-layer P95=1845.715510ms |
| TEAM | Đã điền | Thành viên, phân công, INDIVIDUAL, môi trường và nguồn AI hỗ trợ |
| Checker lần gần nhất | Đạt | check_lab.py --with-tests: 0 failed checks; 104 passed, 3 integration deselected |
| Commit/push và nộp bài | Chưa thực hiện | Chưa xác lập commit nộp hoặc gửi link qua kênh lớp |

## Checkpoint 7 — Kiểm tra và đóng gói nộp

- [x] Ba báo cáo và INDIVIDUAL đầy đủ; giữ số đo và các giới hạn đã đo thật.
- [x] Bốn JSON đạt schema, model roles, generation metadata, pair_sources,
  nguồn/ID, phép tính và source hashes; không gọi lại API trong kiểm tra nộp.
- [x] Rà toàn bộ nội dung Git index: không chứa giá trị secret cấu hình trong
  `.env`, không có token/private key; PII trong source/evidence là mẫu lab.
  Họ tên/MSSV trong TEAM là thông tin thành viên được cung cấp để nộp bài.
- [x] `.env`, virtualenv và cache không được đưa vào index.
- [x] Repo đã công khai và đổi đúng mẫu tên nhóm EvalGuard; origin dùng URL mới.
- [x] `.gitattributes` giữ nguyên byte JSON fixture/evidence giữa Windows/Linux;
  JSON fixtures không đổi nội dung so với starter, chỉ khác lưu trữ xuống dòng.
- [x] Export đúng Git index sang thư mục riêng không có `.env`; checker kèm
  tests đạt 104 passed, 3 integration deselected, 0 failed checks.
- [x] `git diff --cached --check` đạt; toàn bộ source hashes trong index khớp batch live.
- [ ] Chốt commit source/evidence và tag `day24-submission-20261012`.
- [ ] Push source/evidence, ghi SHA trong TEAM và xác nhận đúng revision GitHub.
- [ ] Gửi link repo và SHA qua kênh coach; đang chờ tên/link kênh nhận bài.

## Phần cần xử lý ở các checkpoint tiếp theo

- [x] Xác minh runtime/Docker sau khi giải phóng ổ C.
- [x] Chạy lại Phase C bằng prompt đã sửa; clean allowed=8/8 và attacks=19/20.
- [x] Cập nhật báo cáo từ batch mới, giữ số đo thật và scope input_layers_sequential.
- [x] Checker và unit tests cuối đạt; .env/cache/virtualenv được Git ignore.
- [x] Rà toàn bộ files có thể đưa vào Git: không chứa giá trị key/token cấu hình trong .env;
  dữ liệu PII trong artifacts là fixture giả lập, TEAM chỉ giữ danh tính được cung cấp.
- [ ] Chuẩn bị commit theo yêu cầu nộp.
- [ ] Ghi SHA, push và gửi một link repo/commit qua kênh coach khi đến bước nộp.

Lượt setup mới làm thay đổi answers nên Phase A/B đã chạy lại để đồng bộ source
hashes và nội dung, không sửa hash báo cáo cũ. Không cần chạy lại các batch này khi
chỉ kiểm tra file đã lưu. Batch guard cũ được giữ tại
artifacts/guard_results_initial.json để đối chiếu thay đổi prompt.
