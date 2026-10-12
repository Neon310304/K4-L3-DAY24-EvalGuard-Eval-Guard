# Đánh giá LLM Judge Phase B

Người phụ trách: Trần Quốc Vượng — 2A202602522.

Run timestamp (UTC): 2026-10-12T05:23:02.551214+00:00; run_kind: live.

Model IDs theo vai trò (cấu hình/ID provider ghi lại, không mặc nhiên xác nhận snapshot):

```json
{
  "generation": [
    "gpt-4o-mini"
  ],
  "evaluator": [],
  "judge": [
    "gpt-4o-mini"
  ],
  "guard": []
}
```
Nguồn: `artifacts/judge_results.json`. A lấy đúng answer pipeline; B lấy đúng model_answer của human fixture; reference lấy ground_truth của test set. Năm IDs cố định: 1, 5, 12, 21, 41; hai lượt/cặp, lượt hai quy về A/B gốc.

Nguồn candidates/reference đã đối chiếu bằng nội dung và SHA256:

```json
{
  "A": "artifacts/answers_50q.json:answer",
  "B": "fixtures/human_labels_10q.json:model_answer",
  "reference": "fixtures/test_set_50q.json:ground_truth"
}
```

```json
{
  "answers_50q.json": "db39b713f8872579f5d05641272608595f6ef61f2002def3585095b7cb34a0e9",
  "test_set_50q.json": "0e87f26e020a32c62ea0864940720618f39600b9d3378193704cf2f86e88446d",
  "human_labels_10q.json": "e72338bd99c3d0165348c11997735bbb87c978fe018c24dfd29c9801d5c2b2c1"
}
```

`winner_pass2` và `scores_pass2` đã quy về A/B gốc. `reasoning_pass2` giữ nguyên lời API theo thứ tự swapped: local A = B gốc, local B = A gốc. Khi đọc reasoning lượt hai cần đổi danh tính theo quy tắc này.

## Năm cặp và hai lượt

| ID | Pass 1 | Pass 2 (gốc) | Final | Consistent | Scores 1 | Scores 2 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | B | B | B | True | {'A': 0.0, 'B': 1.0} | {'A': 0.0, 'B': 1.0} |
| 5 | A | A | A | True | {'A': 1.0, 'B': 0.0} | {'A': 1.0, 'B': 0.3} |
| 12 | B | B | B | True | {'A': 0.2, 'B': 1.0} | {'A': 0.0, 'B': 1.0} |
| 21 | B | B | B | True | {'A': 0.7, 'B': 1.0} | {'A': 0.7, 'B': 1.0} |
| 41 | A | A | A | True | {'A': 1.0, 'B': 0.0} | {'A': 1.0, 'B': 0.0} |

### Cặp 1

```json
{
  "question_id": 1,
  "question": "Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?",
  "answer_a": "Context không cung cấp thông tin về số ngày nghỉ khi kết hôn. Do đó, tôi không thể trả lời câu hỏi này.",
  "answer_b": "Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn.",
  "winner_pass1": "B",
  "winner_pass2": "B",
  "final_winner": "B",
  "reasoning_pass1": "Answer B provides the correct information directly from the reference, stating that employees are entitled to 3 days of paid leave for marriage. Answer A, on the other hand, fails to provide any relevant information and incorrectly claims that the context does not provide the necessary details. Therefore, Answer B is more accurate and complete.",
  "reasoning_pass2": "Answer A accurately reflects the information provided in the reference, stating that employees are entitled to 3 days of paid leave for marriage. Answer B incorrectly claims that the context does not provide this information, which is not true as the reference clearly states it. Therefore, Answer A is both accurate and complete, while Answer B is inaccurate and incomplete.",
  "position_consistent": true,
  "scores_pass1": {
    "A": 0.0,
    "B": 1.0
  },
  "scores_pass2": {
    "A": 0.0,
    "B": 1.0
  }
}
```

### Cặp 5

```json
{
  "question_id": 5,
  "question": "Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?",
  "answer_a": "Theo quy trình mua sắm phiên bản 2.2, để mua thiết bị trị giá 55 triệu VNĐ, cần được phê duyệt bởi Tổng Giám đốc (CEO). Tài liệu nguồn: mua_sam.md.",
  "answer_b": "Cần Giám đốc phòng ban phê duyệt.",
  "winner_pass1": "A",
  "winner_pass2": "A",
  "final_winner": "A",
  "reasoning_pass1": "Answer A accurately states that purchases over 50 million VNĐ require approval from the CEO, which aligns with the reference. It is complete in providing the necessary information and cites a source. Answer B incorrectly states that the department director's approval is sufficient, which does not meet the requirement outlined in the reference.",
  "reasoning_pass2": "Answer B accurately identifies that the approval for a purchase over 50 million VNĐ must come from the CEO, which aligns with the reference. It also provides additional context by mentioning the procurement process version and a source document, enhancing completeness. Answer A incorrectly states that the department director's approval is sufficient, which is not in line with the reference.",
  "position_consistent": true,
  "scores_pass1": {
    "A": 1.0,
    "B": 0.0
  },
  "scores_pass2": {
    "A": 1.0,
    "B": 0.3
  }
}
```

### Cặp 12

```json
{
  "question_id": 12,
  "question": "Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là bao nhiêu?",
  "answer_a": "Trong chính sách thưởng Tết phiên bản 2.0, không có thông tin cụ thể về mức thưởng tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên. Thưởng Tết được tính dựa trên kết quả đánh giá hiệu suất cá nhân (60%) và kết quả kinh doanh của công ty (40%). Bạn có thể tham khảo thêm trong tài liệu \"Chính sách thưởng Tết\".",
  "answer_b": "Nhân viên được thưởng Tết tối thiểu 1 tháng lương.",
  "winner_pass1": "B",
  "winner_pass2": "B",
  "final_winner": "B",
  "reasoning_pass1": "Answer B accurately states the minimum Tet bonus for employees with 6 months or more of service, which is 1 month's salary, as per the reference. Answer A fails to provide this critical information and instead discusses performance evaluation criteria, which is not relevant to the question asked. Therefore, Answer B is more accurate and complete.",
  "reasoning_pass2": "Answer A accurately states that employees with 6 months or more of service are entitled to a minimum of 1 month's salary as a Tet bonus, which aligns with the reference. Answer B, however, fails to provide the specific minimum amount and introduces irrelevant details about performance evaluation and company results, making it less complete and concise.",
  "position_consistent": true,
  "scores_pass1": {
    "A": 0.2,
    "B": 1.0
  },
  "scores_pass2": {
    "A": 0.0,
    "B": 1.0
  }
}
```

### Cặp 21

```json
{
  "question_id": 21,
  "question": "Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?",
  "answer_a": "Nhân viên Senior có 9 năm thâm niên sẽ được nghỉ 18 ngày phép năm (15 ngày phép cơ bản + 3 ngày phép cộng thêm cho 9 năm thâm niên). \n\nVề lương, nếu nhân viên này nghỉ phép không lương, trong thời gian nghỉ, họ sẽ không được hưởng lương và các khoản phụ cấp. Tuy nhiên, nếu nghỉ phép năm, họ vẫn sẽ nhận lương bình thường. \n\nThông tin này được lấy từ tài liệu \"Chính sách nghỉ phép năm (Phiên bản 2024)\" và \"Chính sách nghỉ phép không lương (phiên bản 1.2)\".",
  "answer_b": "Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu.",
  "winner_pass1": "B",
  "winner_pass2": "B",
  "final_winner": "B",
  "reasoning_pass1": "Answer B provides the correct number of leave days and salary range concisely and accurately, aligning closely with the reference. Answer A, while accurate, includes unnecessary details about unpaid leave that do not directly address the question, making it less concise.",
  "reasoning_pass2": "Answer A provides a clear and accurate summary of the vacation days and salary range for a Senior employee with 9 years of experience, directly aligning with the reference. Answer B, while accurate in the vacation days and salary, introduces unnecessary details about unpaid leave that are not relevant to the question, making it less concise. Therefore, A is preferred for its accuracy and conciseness.",
  "position_consistent": true,
  "scores_pass1": {
    "A": 0.7,
    "B": 1.0
  },
  "scores_pass2": {
    "A": 0.7,
    "B": 1.0
  }
}
```

### Cặp 41

```json
{
  "question_id": 41,
  "question": "Nhân viên được nghỉ bao nhiêu ngày phép năm?",
  "answer_a": "Nhân viên chính thức được hưởng **15 ngày phép năm** có lương, theo chính sách nghỉ phép năm (Phiên bản 2024) ban hành ngày 01/01/2024. Chính sách này thay thế hoàn toàn phiên bản 1.0 ban hành ngày 01/01/2023.",
  "answer_b": "Nhân viên được nghỉ 12 ngày phép năm.",
  "winner_pass1": "A",
  "winner_pass2": "A",
  "final_winner": "A",
  "reasoning_pass1": "Answer A accurately reflects the current policy (version 2024) stating that employees receive 15 days of paid leave, which is the correct and updated information. Answer B incorrectly states the outdated policy of 12 days, which has been replaced. Therefore, Answer A is more accurate and complete.",
  "reasoning_pass2": "Answer B accurately reflects the current policy for 2024, stating that employees are entitled to 15 days of paid leave, which is the correct and updated information. Answer A incorrectly states 12 days, which is outdated and no longer applicable. Additionally, Answer B provides context about the policy change, enhancing its completeness. Therefore, Answer B is more accurate and complete than Answer A.",
  "position_consistent": true,
  "scores_pass1": {
    "A": 1.0,
    "B": 0.0
  },
  "scores_pass2": {
    "A": 1.0,
    "B": 0.0
  }
}
```

## Position và verbosity

```json
{
  "total_judged": 5,
  "position_bias_count": 0,
  "position_bias_rate": 0.0,
  "verbosity_bias": 0.4,
  "verbosity_details": {
    "a_wins_a_longer": 2,
    "b_wins_b_longer": 0,
    "total_decisive": 5
  },
  "interpretation": "0/5 order-inconsistent comparisons; longer answers won 2/5 decisive cases. These are descriptive signals; inspect accuracy and completeness before claiming causal position or verbosity bias. Small samples limit generalization."
}
```

Position inconsistency = 0/5 = 0.000000. Winner dài hơn: A thắng và dài hơn 2 cặp; B thắng và dài hơn 0 cặp; tổng decisive 5; verbosity rate = 0.400000.


Bất đồng sau swap chỉ cho thấy nhạy với thứ tự/lượt gọi; chưa xác định nguyên nhân. Verbosity là tỷ lệ winner dài hơn theo số ký tự trong các lượt decisive; answer dài có thể thắng vì đủ ý. Cần đọc reference và reasoning của từng cặp trước khi gán thiên lệch. Tie không được đổi thành nhãn tốt/xấu.

## Calibration đúng model_answer

Binary helper chỉ nhận question, model_answer gốc và reference; human_label, human_note và tỷ lệ nhãn không được gửi vào prompt. Nhãn người chỉ dùng sau khi đã tạo đủ mười binary judgments.

| ID | Model answer gốc | Judge | Human | Agree | Reasoning |
| --- | --- | --- | --- | --- | --- |
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | 1 | True | Câu trả lời chính xác theo thông tin trong tài liệu tham khảo, nêu rõ số ngày nghỉ và điều kiện không trừ vào phép năm. |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 0 | True | Câu trả lời sai vì không nêu đúng người phê duyệt theo chính sách, cần Tổng Giám đốc chứ không phải Giám đốc phòng ban. |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | 1 | True | Câu trả lời chính xác theo thông tin trong reference, nêu rõ điều kiện và mức thưởng cho nhân viên chính thức có từ 6 tháng trở lên. |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | 1 | True | Câu trả lời chính xác theo reference, nêu rõ số ngày phép và khoảng lương cho nhân viên Senior có 9 năm thâm niên. |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | 1 | True | Câu trả lời chính xác theo reference, nêu rõ rằng nhân viên phải hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | 0 | True | Câu trả lời sai vì không đề cập đến sự cần thiết có sự phê duyệt của Kế toán trưởng bên cạnh Trưởng phòng. Ngoài ra, phí phạt được tính cho quá hạn 15 ngày, không phải là 2% trên tổng số tiền tạm ứng. |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | 1 | True | Câu trả lời cung cấp đúng số ngày phép và tổng phụ cấp hàng tháng theo thông tin trong tài liệu tham khảo. |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 0 | True | Câu trả lời sai vì dựa vào chính sách cũ (v2023) thay vì chính sách hiện hành (v2024) là 15 ngày phép năm. |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | 1 | True | Câu trả lời chính xác theo reference, nêu rõ rằng nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần, đồng thời không bỏ qua điều kiện cần có sự phê duyệt của trưởng phòng. |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | 0 | True | Câu trả lời sai vì cho phép sử dụng VPN cá nhân trong khi chính sách rõ ràng cấm điều này. |

Observed agreement p_o=1.000000; chance agreement p_e=0.520000. κ=(p_o-p_e)/(1-p_e)=**1.000000**. Điều kiện bonus κ>0.6: True.

Judge có 6 nhãn 1/4 nhãn 0; human có 6 nhãn 1/4 nhãn 0. p_e=(6/10 × 6/10) + (4/10 × 4/10). IDs/thứ tự: [1, 5, 12, 21, 23, 29, 33, 41, 46, 50].

| Judge \ Human | 0 | 1 |
| --- | --- | --- |
| 0 | 4 | 0 |
| 1 | 0 | 6 |

## Đọc nội dung và độ tin cậy của reasoning

Độ dài tính bằng `len(str)` của Python, gồm khoảng trắng và Markdown. Độ dài không phải tiêu chí độc lập để đổi winner.

| ID | Đối chiếu reference | Winner | Độ dài A/B | Nhận xét kiểm chứng |
| --- | --- | --- | --- | --- |
| 1 | B đúng 3 ngày; A từ chối trả lời | B | 103/57 | B ngắn hơn nhưng đủ ý chính; pairwise không nhận contexts nên chưa thể kết luận A nói sai về contexts đã retrieve. |
| 5 | A đúng CEO; B nhầm giám đốc phòng ban | A | 147/33 | A dài hơn và thắng vì đúng ngưỡng phê duyệt. |
| 12 | B nêu mức tối thiểu 1 tháng; A bỏ sót mức tối thiểu | B | 318/50 | A dài hơn nhưng thiếu số tiền cần hỏi; phần trọng số hiệu suất không bù được ý thiếu. |
| 21 | B đủ 18 ngày và lương 20–35 triệu; A bỏ sót khoảng lương | B | 458/82 | B thắng hợp lý; reasoning pass 2 gọi A gốc accurate cả về lương dù A không đưa khoảng lương. |
| 41 | A dùng v2024 là 15 ngày; B dùng v2023 là 12 ngày | A | 209/37 | A dài hơn và thắng vì đúng phiên bản; chưa tách được hiệu ứng độ dài khỏi nội dung. |

Ở lượt hai, API nhận thứ tự B/A. Trường `winner_pass2` và `scores_pass2` đã được quy về danh tính A/B ban đầu, còn `reasoning_pass2` được lưu nguyên văn của lượt swapped nên các từ ‘Answer A/B’ trong đoạn reasoning đó chỉ vị trí của lượt hai. Ví dụ ở ID 1, reasoning pass 2 gọi local A là câu 3 ngày; đó là B gốc. Không có cặp bất đồng sau quy đổi (0/5), vì vậy batch này không cho một ví dụ live về tie do swap; test `test_swap_conversion_and_calls` kiểm tra trường hợp bất đồng.

Reasoning nhị phân cần đối chiếu từng mệnh đề: ID 1 có judge=human=1, nhưng reasoning nói answer nêu điều kiện ‘không trừ vào phép năm’ mà model_answer gốc không viết điều đó. ID 46 cũng có judge=human=1, nhưng reasoning nói answer đã nêu phê duyệt trưởng phòng; answer gốc chỉ nói nghỉ không lương. Các lệch mô tả này không đổi nhãn đã đo. Riêng ID 46 cần người review xác định phê duyệt trưởng phòng có là điều kiện thiết yếu theo rubric hay không; cả human và judge đồng ý 1 vẫn có thể cùng bỏ sót một điều kiện.

ID 29 có judge=human=0; reference yêu cầu cả Trưởng phòng và Kế toán trưởng, cùng phí 2% × 8.000.000 × 15/30 = 80.000 VNĐ. Model_answer thiếu người duyệt thứ hai và số tiền pro-rata. Reasoning nói phí không phải 2% trên tổng tạm ứng dễ gây nhầm: 8 triệu vẫn là gốc tính phí, thiếu sót là thời gian 15 ngày và kết quả cụ thể. Không có binary case bất đồng nhãn; các lỗi mô tả cho thấy κ chỉ đo agreement với nhãn người trên tập này, không chứng minh rationale luôn bám từng mệnh đề.

Nhận xét thủ công gắn fingerprint toàn bộ JSON (serialize sort_keys=True, ensure_ascii=False, UTF-8): `abdb0cb266f86c4c197414fcc3b58592b71ebc14e6be7b350ab6815e2d5cbdc4`. Khi runner ghi batch khác, cần review lại.

## Giới hạn và cách dùng judge

Chỉ có năm cặp và mười nhãn; κ trên mẫu nhỏ không chứng minh judge đúng cho mọi chính sách. Ground truth và human labels cũng cần được review khi có bất đồng. Giữ swap-and-average, reference và temperature=0; lưu model/prompt khi so sánh các lần chạy. Dùng judge để ưu tiên review, kết hợp người đọc các case thiếu điều kiện, phủ định hoặc sai phiên bản trước quyết định triển khai.
