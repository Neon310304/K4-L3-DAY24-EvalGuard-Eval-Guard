# Phân tích lỗi Phase A

Người phụ trách: Trần Quốc Vượng — 2A202602522.

Run timestamp (UTC): 2026-10-12T05:35:59.168641+00:00; run_kind: live.

Model IDs theo vai trò (cấu hình/ID provider ghi lại, không mặc nhiên xác nhận snapshot):

```json
{
  "generation": [
    "gpt-4o-mini"
  ],
  "evaluator": [
    "gpt-4o-mini",
    "text-embedding-3-small"
  ],
  "judge": [],
  "guard": []
}
```
Nguồn: `artifacts/ragas_50q.json`, `artifacts/answers_50q.json`. Có 50 answers; 50 LLM, 0 extractive fallback. Contexts lấy từ BGE-M3/BM25/Qdrant và FlashRank, không lấy từ ground truth. M4 gọi RAGAS 0.1.22 với bốn metric thật; không thay NaN bằng số giả. Điểm và metadata giữ từ batch live; bottom/matrix/diagnosis được dựng lại từ per_question đã lưu. Các gợi ý nguồn theo chủ đề trong Task 3 chỉ phục vụ review, không tham gia retrieval/generation.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
| --- | --- | --- | --- |
| faithfulness | 0.819167 | 0.563727 | 0.808333 |
| answer_relevancy | 0.272002 | 0.375834 | 0.213453 |
| context_precision | 0.591667 | 0.675000 | 0.558333 |
| context_recall | 0.550000 | 0.450000 | 0.583333 |
| avg_score | 0.558209 | 0.516140 | 0.540863 |

## Bottom 10 và bằng chứng

| Rank | ID | Question | Distribution | Mean | Worst metric | Diagnosis | Fix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 48 | Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không? | adversarial | 0.0833 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Trong tài liệu "Chính sách bảo hiểm sức khỏe" phiên bản 1.5, không có thông tin cụ thể về việc nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI hay không.». Reference nêu: «KHÔNG. Nhân viên thử việc chưa được hưởng gói PVI. Chỉ được tham gia BHXH bắt buộc. Đây là negation trap — pipeline hay nhầm vì tài liệu PVI không đề cập rõ exclusion.». Nguồn trong contexts: bao_hiem_suc_khoe.md, nghi_om.md. Top contexts thiếu nguồn cần đối chiếu thu_viec.md; chưa có log candidates để tách lỗi search khỏi rerank. Thiếu exclusion PVI trong chính sách thử việc; không suy ra eligibility từ gói gia đình/bồi hoàn. | Với câu hỏi «Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không?», kiểm tra candidates trước/sau rerank tại bao_hiem_suc_khoe.md, thu_viec.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. |
| 2 | 16 | Tài khoản VPN bị khóa tự động sau bao nhiêu ngày không hoạt động? | factual | 0.125 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Trong context hiện tại không có thông tin về việc tài khoản VPN bị khóa tự động sau bao nhiêu ngày không hoạt động. Bạn có thể cần tham khảo tài liệu khác để tì». Reference nêu: «Tài khoản VPN tự động bị khóa sau 60 ngày không hoạt động. Để kích hoạt lại cần gửi ticket IT kèm xác nhận quản lý trực tiếp, thời gian xử lý 1-2 ngày làm việc.». Nguồn trong contexts: vpn_truy_cap.md, tam_ung.md, mat_khau_v1.md. Đã lấy đúng tên file nhưng answer chưa đáp ứng; kiểm tra passage thiếu điều kiện hay generation bỏ sót căn cứ. Metadata source không chứng minh passage đã trả lời được câu hỏi. Đoạn VPN đang nói ngắt phiên sau 12 giờ, không phải khóa tài khoản sau 60 ngày. | Với câu hỏi «Tài khoản VPN bị khóa tự động sau bao nhiêu ngày không hoạt động?», kiểm tra candidates trước/sau rerank tại vpn_truy_cap.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. |
| 3 | 26 | Nhân viên vừa kết hôn và cùng tuần đó có con kết hôn. Tổng số ngày nghỉ đặc biệt có lương là bao nhiêu? | multi_hop | 0.1667 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về chính sách nghỉ đặc biệt có lương cho nhân viên vừa kết hôn và có con kết hôn. Do đó, tôi không thể xác định tổng số ngày ng». Reference nêu: «Kết hôn bản thân: 3 ngày. Con kết hôn: 1 ngày. Tổng: 4 ngày làm việc có lương, tất cả không trừ vào phép năm.». Nguồn trong contexts: mentor_buddy.md, nghi_phep_khong_luong.md, nghi_om.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank. | Với câu hỏi «Nhân viên vừa kết hôn và cùng tuần đó có con kết hôn. Tổng số ngày nghỉ đặc biệt có lương là bao nhiêu?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. Thu đủ từng căn cứ trước khi cộng số ngày hoặc suy điều kiện áp dụng. |
| 4 | 6 | Thông tin lương thuộc cấp độ phân loại dữ liệu nào? | factual | 0.2083 | faithfulness | Answer chưa trả lời được yêu cầu: «Trong context hiện tại, không có thông tin cụ thể về việc phân loại dữ liệu liên quan đến thông tin lương. Do đó, không thể xác định cấp độ phân loại dữ liệu ch». Reference nêu: «Theo quy chế chi trả lương, thông tin lương được phân loại là dữ liệu Bí mật (cấp 3), cấm chia sẻ với đồng nghiệp. Phải mã hóa khi truyền và hạn chế truy cập theo need-to-know.». Nguồn trong contexts: phan_loai_du_lieu.md. Top contexts thiếu nguồn cần đối chiếu ky_luong.md; chưa có log candidates để tách lỗi search khỏi rerank. | Với câu hỏi «Thông tin lương thuộc cấp độ phân loại dữ liệu nào?», kiểm tra candidates trước/sau rerank tại ky_luong.md, phan_loai_du_lieu.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. |
| 5 | 1 | Nhân viên được nghỉ bao nhiêu ngày khi kết hôn? | factual | 0.25 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về số ngày nghỉ khi kết hôn. Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn, không trừ vào phép năm.». Nguồn trong contexts: nghi_om.md, hoan_chi_dao_tao.md, nghi_phep_khong_luong.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank. | Với câu hỏi «Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. |
| 6 | 8 | Nhân viên được nghỉ bao nhiêu ngày khi cha hoặc mẹ mất? | factual | 0.25 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về số ngày nghỉ khi cha hoặc mẹ mất. Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Nhân viên được nghỉ 3 ngày làm việc có lương khi cha mẹ mất (tang lễ). Không trừ vào phép năm.». Nguồn trong contexts: nghi_om.md, nghi_phep_nam_v2024.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank. | Với câu hỏi «Nhân viên được nghỉ bao nhiêu ngày khi cha hoặc mẹ mất?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. |
| 7 | 9 | Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con? | factual | 0.25 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về số ngày nghỉ cho nam nhân viên khi vợ sinh con. Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Nam nhân viên được nghỉ 5 ngày làm việc liên tục khi vợ sinh con, không trừ vào phép năm.». Nguồn trong contexts: nghi_om.md, nghi_phep_khong_luong.md, nghi_phep_nam_v2024.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank. | Với câu hỏi «Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. |
| 8 | 19 | Thời gian thử việc tiêu chuẩn và tối đa (dành cho Manager trở lên) là bao nhiêu ngày? | factual | 0.25 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về thời gian thử việc tiêu chuẩn và tối đa (dành cho Manager trở lên). Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Thời gian thử việc tiêu chuẩn là 60 ngày. Đối với vị trí Manager trở lên, có thể kéo dài đến 90 ngày.». Nguồn trong contexts: cong_tac_phi.md, nghi_phep_nam_v2024.md, mentor_buddy.md. Top contexts thiếu nguồn cần đối chiếu thu_viec.md; chưa có log candidates để tách lỗi search khỏi rerank. | Với câu hỏi «Thời gian thử việc tiêu chuẩn và tối đa (dành cho Manager trở lên) là bao nhiêu ngày?», kiểm tra candidates trước/sau rerank tại thu_viec.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. |
| 9 | 43 | Mật khẩu phải có tối thiểu bao nhiêu ký tự? | adversarial | 0.25 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về yêu cầu mật khẩu, vì vậy không thể trả lời câu hỏi này.». Reference nêu: «Theo v2.0 HIỆN HÀNH: tối thiểu 12 ký tự. Chính sách v1.0 (đã thay thế) yêu cầu 8 ký tự. RAG có thể lấy cả 2 tài liệu — câu trả lời đúng là 12 ký tự.». Nguồn trong contexts: bao_mat_su_co.md, phan_loai_du_lieu.md. Top contexts thiếu nguồn cần đối chiếu mat_khau_v2.md; chưa có log candidates để tách lỗi search khỏi rerank. | Với câu hỏi «Mật khẩu phải có tối thiểu bao nhiêu ký tự?», kiểm tra candidates trước/sau rerank tại mat_khau_v2.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. Giữ cả v1/v2, chọn phiên bản theo thời điểm được hỏi; không xóa policy cũ. |
| 10 | 32 | Nhân viên mới cấp Manager có thời hạn thử việc 90 ngày, đang trong tháng thứ 3, có BẮT BUỘC tham dự buổi đào tạo nội bộ của phòng ban không? Tại sao? | multi_hop | 0.2708 | answer_relevancy | Answer chưa trả lời được yêu cầu: «Theo chính sách đào tạo nội bộ (phiên bản 1.3, có hiệu lực từ 01/01/2024), không có thông tin cụ thể nào đề cập đến việc nhân viên mới cấp Manager có bắt buộc t». Reference nêu: «Có, BẮT BUỘC. Theo chính sách đào tạo nội bộ, nhân viên mới trong 6 tháng đầu phải tham gia tất cả các buổi đào tạo của phòng ban. Nhân viên tháng thứ 3 (đang thử việc) vẫn nằm trong phạm vi 6 tháng đầu.». Nguồn trong contexts: dao_tao_noi_bo.md, hoan_chi_dao_tao.md, mentor_buddy.md. Đã lấy đúng tên file nhưng answer chưa đáp ứng; kiểm tra passage thiếu điều kiện hay generation bỏ sót căn cứ. Metadata source không chứng minh passage đã trả lời được câu hỏi. Context đào tạo thiếu nguyên câu quy định nhân viên mới trong 6 tháng đầu. | Với câu hỏi «Nhân viên mới cấp Manager có thời hạn thử việc 90 ngày, đang trong tháng thứ 3, có BẮT BUỘC tham dự buổi đào tạo nội bộ của phòng ban không? Tại sao?», kiểm tra candidates trước/sau rerank tại dao_tao_noi_bo.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. Thu đủ từng căn cứ trước khi cộng số ngày hoặc suy điều kiện áp dụng. |

Diagnosis theo metric là giả thuyết cần đối chiếu. Faithfulness thấp gợi ý answer chưa được contexts hỗ trợ; recall thấp gợi ý thiếu căn cứ; precision thấp gợi ý chunks không hữu ích; relevancy thấp gợi ý trả lời lệch hoặc thiếu yêu cầu. Không coi metric đơn lẻ là bằng chứng đủ để kết luận nguyên nhân.

### Câu 48 — adversarial

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 0.333333 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không?

Answer thực tế:

> Trong tài liệu "Chính sách bảo hiểm sức khỏe" phiên bản 1.5, không có thông tin cụ thể về việc nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI hay không. Do đó, phần này không tìm thấy trong context. Bạn có thể cần liên hệ với phòng Nhân sự để biết thêm chi tiết.

Reference:

> KHÔNG. Nhân viên thử việc chưa được hưởng gói PVI. Chỉ được tham gia BHXH bắt buộc. Đây là negation trap — pipeline hay nhầm vì tài liệu PVI không đề cập rõ exclusion.

Contexts đã retrieve/rerank:

```json
[
  "[source: bao_hiem_suc_khoe.md | title: Chính sách bảo hiểm sức khỏe | version: 1.5 | effective_date: 01/04/2024]\nội trú, ngoại trú và nha khoa.\n\n## Gói gia đình\nNhân viên có thể đăng ký thêm gói bảo hiểm cho người thân (vợ/chồng, con dưới 18 tuổi) với hạn mức **50.000.000 VNĐ/năm/người**.",
  "[source: bao_hiem_suc_khoe.md | title: Chính sách bảo hiểm sức khỏe | version: 1.5 | effective_date: 01/04/2024]\nhấu trừ lương hàng tháng.\n\n## Quy trình sử dụng\nNhân viên xuất trình thẻ bảo hiểm PVI tại các bệnh viện/phòng khám trong danh sách liên kết. Trường hợp khám ngoài danh sách, nhân viên thanh toán trước và nộp hồ sơ bồi hoàn trong vòng 30 ngày.",
  "[source: nghi_om.md | title: Chính sách nghỉ ốm | version: 1.0 | effective_date: 01/01/2024]\n nhận đủ 100% lương cơ bản.\n\n## Nghỉ ốm dài hạn\nTrường hợp nghỉ ốm trên 30 ngày/năm, nhân viên cần liên hệ phòng Nhân sự để được hướng dẫn chế độ bảo hiểm dài hạn. Công ty có quyền yêu cầu khám sức khỏe tổng quát trước khi nhân viên quay lại làm việc."
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Trong tài liệu "Chính sách bảo hiểm sức khỏe" phiên bản 1.5, không có thông tin cụ thể về việc nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI hay không.». Reference nêu: «KHÔNG. Nhân viên thử việc chưa được hưởng gói PVI. Chỉ được tham gia BHXH bắt buộc. Đây là negation trap — pipeline hay nhầm vì tài liệu PVI không đề cập rõ exclusion.». Nguồn trong contexts: bao_hiem_suc_khoe.md, nghi_om.md. Top contexts thiếu nguồn cần đối chiếu thu_viec.md; chưa có log candidates để tách lỗi search khỏi rerank. Thiếu exclusion PVI trong chính sách thử việc; không suy ra eligibility từ gói gia đình/bồi hoàn.

Hướng sửa cần thử: Với câu hỏi «Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không?», kiểm tra candidates trước/sau rerank tại bao_hiem_suc_khoe.md, thu_viec.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.

### Câu 16 — factual

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 0.500000 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Tài khoản VPN bị khóa tự động sau bao nhiêu ngày không hoạt động?

Answer thực tế:

> Trong context hiện tại không có thông tin về việc tài khoản VPN bị khóa tự động sau bao nhiêu ngày không hoạt động. Bạn có thể cần tham khảo tài liệu khác để tìm thông tin này.

Reference:

> Tài khoản VPN tự động bị khóa sau 60 ngày không hoạt động. Để kích hoạt lại cần gửi ticket IT kèm xác nhận quản lý trực tiếp, thời gian xử lý 1-2 ngày làm việc.

Contexts đã retrieve/rerank:

```json
[
  "[source: vpn_truy_cap.md | title: Chính sách VPN và truy cập từ xa | version: 1.3 | effective_date: 01/04/2024]\ná nhân (NordVPN, ExpressVPN) trong mạng công ty\n- Phiên VPN tự động ngắt sau 12 giờ, cần đăng nhập lại",
  "[source: tam_ung.md | title: Chính sách tạm ứng | version: 1.0 | effective_date: 01/01/2024]\nngày kết thúc chuyến công tác.\n\n## Phạt quá hạn\nKhoản tạm ứng chưa thanh toán sau 15 ngày sẽ bị tính phí **2%/tháng** trên số tiền chưa hoàn ứng. Phí này được khấu trừ vào lương tháng kế tiếp.",
  "[source: mat_khau_v1.md | title: Chính sách mật khẩu (Phiên bản cũ) | version: 1.0 | effective_date: 01/01/2022]\n nhân dễ đoán làm mật khẩu.\n\n## Chu kỳ thay đổi\nMật khẩu phải được thay đổi **mỗi 90 ngày**. Hệ thống sẽ tự động nhắc nhở trước 7 ngày. Mật khẩu mới không được trùng với 3 mật khẩu gần nhất.\n\n## Lưu ý\n"
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Trong context hiện tại không có thông tin về việc tài khoản VPN bị khóa tự động sau bao nhiêu ngày không hoạt động. Bạn có thể cần tham khảo tài liệu khác để tì». Reference nêu: «Tài khoản VPN tự động bị khóa sau 60 ngày không hoạt động. Để kích hoạt lại cần gửi ticket IT kèm xác nhận quản lý trực tiếp, thời gian xử lý 1-2 ngày làm việc.». Nguồn trong contexts: vpn_truy_cap.md, tam_ung.md, mat_khau_v1.md. Đã lấy đúng tên file nhưng answer chưa đáp ứng; kiểm tra passage thiếu điều kiện hay generation bỏ sót căn cứ. Metadata source không chứng minh passage đã trả lời được câu hỏi. Đoạn VPN đang nói ngắt phiên sau 12 giờ, không phải khóa tài khoản sau 60 ngày.

Hướng sửa cần thử: Với câu hỏi «Tài khoản VPN bị khóa tự động sau bao nhiêu ngày không hoạt động?», kiểm tra candidates trước/sau rerank tại vpn_truy_cap.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.

### Câu 26 — multi_hop

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 0.666667 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Nhân viên vừa kết hôn và cùng tuần đó có con kết hôn. Tổng số ngày nghỉ đặc biệt có lương là bao nhiêu?

Answer thực tế:

> Context không cung cấp thông tin về chính sách nghỉ đặc biệt có lương cho nhân viên vừa kết hôn và có con kết hôn. Do đó, tôi không thể xác định tổng số ngày nghỉ đặc biệt có lương trong trường hợp này. Bạn có thể tham khảo thêm các tài liệu khác liên quan đến chính sách nghỉ phép để có thông tin chi tiết hơn.

Reference:

> Kết hôn bản thân: 3 ngày. Con kết hôn: 1 ngày. Tổng: 4 ngày làm việc có lương, tất cả không trừ vào phép năm.

Contexts đã retrieve/rerank:

```json
[
  "[source: mentor_buddy.md | title: Chương trình Mentor & Buddy | version: 1.0 | effective_date: 01/06/2024]\nhân viên cùng phòng ban, thâm niên từ 6 tháng.\n\n## Quy tắc quan trọng\nMentor và Buddy phải là **hai người khác nhau** để đảm bảo nhân viên mới có nhiều nguồn hỗ trợ đa dạng. Quản lý trực tiếp không được làm Mentor hoặc Buddy.\n\n## Thời gian chương trình\n",
  "[source: nghi_phep_khong_luong.md | title: Chính sách nghỉ phép không lương | version: 1.2 | effective_date: 01/07/2023]\nc điều hành (CEO)**.\n\n## Ảnh hưởng đến phúc lợi\nTrong thời gian nghỉ không lương, nhân viên không được hưởng lương và các khoản phụ cấp. Bảo hiểm y tế vẫn được duy trì nếu nghỉ dưới 14 ngày. Nghỉ trên 14 ngày, nhân viên cần tự đóng phần bảo hiểm của mình.",
  "[source: nghi_om.md | title: Chính sách nghỉ ốm | version: 1.0 | effective_date: 01/01/2024]\n nhận đủ 100% lương cơ bản.\n\n## Nghỉ ốm dài hạn\nTrường hợp nghỉ ốm trên 30 ngày/năm, nhân viên cần liên hệ phòng Nhân sự để được hướng dẫn chế độ bảo hiểm dài hạn. Công ty có quyền yêu cầu khám sức khỏe tổng quát trước khi nhân viên quay lại làm việc."
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về chính sách nghỉ đặc biệt có lương cho nhân viên vừa kết hôn và có con kết hôn. Do đó, tôi không thể xác định tổng số ngày ng». Reference nêu: «Kết hôn bản thân: 3 ngày. Con kết hôn: 1 ngày. Tổng: 4 ngày làm việc có lương, tất cả không trừ vào phép năm.». Nguồn trong contexts: mentor_buddy.md, nghi_phep_khong_luong.md, nghi_om.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank.

Hướng sửa cần thử: Với câu hỏi «Nhân viên vừa kết hôn và cùng tuần đó có con kết hôn. Tổng số ngày nghỉ đặc biệt có lương là bao nhiêu?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. Thu đủ từng căn cứ trước khi cộng số ngày hoặc suy điều kiện áp dụng.

### Câu 6 — factual

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 0.000000 | 0.000000 | 0.833333 | 0.000000 |

Câu hỏi: Thông tin lương thuộc cấp độ phân loại dữ liệu nào?

Answer thực tế:

> Trong context hiện tại, không có thông tin cụ thể về việc phân loại dữ liệu liên quan đến thông tin lương. Do đó, không thể xác định cấp độ phân loại dữ liệu cho thông tin lương.

Reference:

> Theo quy chế chi trả lương, thông tin lương được phân loại là dữ liệu Bí mật (cấp 3), cấm chia sẻ với đồng nghiệp. Phải mã hóa khi truyền và hạn chế truy cập theo need-to-know.

Contexts đã retrieve/rerank:

```json
[
  "[source: phan_loai_du_lieu.md | title: Chính sách phân loại dữ liệu | version: 1.0 | effective_date: 01/06/2024]\ntrình nội bộ, biên bản họp, danh bạ nhân viên |\n| 3 | **Bí mật** | Dữ liệu khách hàng, hợp đồng, chiến lược kinh doanh |\n| 4 | **Tối mật** | Mã nguồn core, bí mật thương mại, kế hoạch M&A |\n\n## Quy tắc xử lý\n- **Công khai**: chia sẻ tự do, không hạn chế\n",
  "[source: phan_loai_du_lieu.md | title: Chính sách phân loại dữ liệu | version: 1.0 | effective_date: 01/06/2024]\np độ | Nhãn | Ví dụ |\n|--------|------|-------|\n| 1 | **Công khai** | Thông tin marketing, bài blog, tuyển dụng |\n| 2 | **Nội bộ** | Quy trình nội bộ, biên bản họp, danh bạ nhân viên |\n",
  "[source: phan_loai_du_lieu.md | title: Chính sách phân loại dữ liệu | version: 1.0 | effective_date: 01/06/2024]\n Giám đốc CNTT, log tất cả truy cập\n\n## Vi phạm\nVi phạm chính sách phân loại dữ liệu sẽ bị xử lý kỷ luật theo Quy chế kỷ luật công ty, mức cao nhất là sa thải và chịu trách nhiệm pháp lý."
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Trong context hiện tại, không có thông tin cụ thể về việc phân loại dữ liệu liên quan đến thông tin lương. Do đó, không thể xác định cấp độ phân loại dữ liệu ch». Reference nêu: «Theo quy chế chi trả lương, thông tin lương được phân loại là dữ liệu Bí mật (cấp 3), cấm chia sẻ với đồng nghiệp. Phải mã hóa khi truyền và hạn chế truy cập theo need-to-know.». Nguồn trong contexts: phan_loai_du_lieu.md. Top contexts thiếu nguồn cần đối chiếu ky_luong.md; chưa có log candidates để tách lỗi search khỏi rerank.

Hướng sửa cần thử: Với câu hỏi «Thông tin lương thuộc cấp độ phân loại dữ liệu nào?», kiểm tra candidates trước/sau rerank tại ky_luong.md, phan_loai_du_lieu.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.

### Câu 1 — factual

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 1.000000 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?

Answer thực tế:

> Context không cung cấp thông tin về số ngày nghỉ khi kết hôn. Do đó, tôi không thể trả lời câu hỏi này.

Reference:

> Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn, không trừ vào phép năm.

Contexts đã retrieve/rerank:

```json
[
  "[source: nghi_om.md | title: Chính sách nghỉ ốm | version: 1.0 | effective_date: 01/01/2024]\n nhận đủ 100% lương cơ bản.\n\n## Nghỉ ốm dài hạn\nTrường hợp nghỉ ốm trên 30 ngày/năm, nhân viên cần liên hệ phòng Nhân sự để được hướng dẫn chế độ bảo hiểm dài hạn. Công ty có quyền yêu cầu khám sức khỏe tổng quát trước khi nhân viên quay lại làm việc.",
  "[source: hoan_chi_dao_tao.md | title: Chính sách hoàn chi đào tạo | version: 1.1 | effective_date: 01/07/2023]\n ty ít nhất 1 năm** sau khi hoàn thành khóa học. Nếu nghỉ việc trước thời hạn cam kết, nhân viên phải hoàn trả **100% chi phí** đào tạo đã được tài trợ.\n\n## Quy trình\n1. Nộp đơn đề xuất đào tạo kèm chương trình chi tiết\n",
  "[source: nghi_phep_khong_luong.md | title: Chính sách nghỉ phép không lương | version: 1.2 | effective_date: 01/07/2023]\nc điều hành (CEO)**.\n\n## Ảnh hưởng đến phúc lợi\nTrong thời gian nghỉ không lương, nhân viên không được hưởng lương và các khoản phụ cấp. Bảo hiểm y tế vẫn được duy trì nếu nghỉ dưới 14 ngày. Nghỉ trên 14 ngày, nhân viên cần tự đóng phần bảo hiểm của mình."
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về số ngày nghỉ khi kết hôn. Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn, không trừ vào phép năm.». Nguồn trong contexts: nghi_om.md, hoan_chi_dao_tao.md, nghi_phep_khong_luong.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank.

Hướng sửa cần thử: Với câu hỏi «Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.

### Câu 8 — factual

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 1.000000 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Nhân viên được nghỉ bao nhiêu ngày khi cha hoặc mẹ mất?

Answer thực tế:

> Context không cung cấp thông tin về số ngày nghỉ khi cha hoặc mẹ mất. Do đó, tôi không thể trả lời câu hỏi này.

Reference:

> Nhân viên được nghỉ 3 ngày làm việc có lương khi cha mẹ mất (tang lễ). Không trừ vào phép năm.

Contexts đã retrieve/rerank:

```json
[
  "[source: nghi_om.md | title: Chính sách nghỉ ốm | version: 1.0 | effective_date: 01/01/2024]\nghỉ sẽ bị trừ vào phép năm.\n\n## Chế độ bảo hiểm\nNhân viên được hưởng chế độ nghỉ ốm tối đa **30 ngày/năm** theo bảo hiểm xã hội. Trong thời gian nghỉ ốm có bảo hiểm, nhân viên được hưởng 75% mức lương đóng bảo hiểm.",
  "[source: nghi_phep_nam_v2024.md | title: Chính sách nghỉ phép năm (Phiên bản 2024) | version: 2.0 | effective_date: 01/01/2024]\n/2024 | Phòng ban: Nhân sự\n\n## Số ngày phép năm\nMỗi nhân viên chính thức được hưởng **15 ngày phép năm** có lương, tăng từ 12 ngày so với chính sách năm 2023. Chính sách này thay thế hoàn toàn phiên bản 1.0 ban hành ngày 01/01/2023.\n\n## Thâm niên công tác\n",
  "[source: nghi_om.md | title: Chính sách nghỉ ốm | version: 1.0 | effective_date: 01/01/2024]\n nhận đủ 100% lương cơ bản.\n\n## Nghỉ ốm dài hạn\nTrường hợp nghỉ ốm trên 30 ngày/năm, nhân viên cần liên hệ phòng Nhân sự để được hướng dẫn chế độ bảo hiểm dài hạn. Công ty có quyền yêu cầu khám sức khỏe tổng quát trước khi nhân viên quay lại làm việc."
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về số ngày nghỉ khi cha hoặc mẹ mất. Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Nhân viên được nghỉ 3 ngày làm việc có lương khi cha mẹ mất (tang lễ). Không trừ vào phép năm.». Nguồn trong contexts: nghi_om.md, nghi_phep_nam_v2024.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank.

Hướng sửa cần thử: Với câu hỏi «Nhân viên được nghỉ bao nhiêu ngày khi cha hoặc mẹ mất?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.

### Câu 9 — factual

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 1.000000 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con?

Answer thực tế:

> Context không cung cấp thông tin về số ngày nghỉ cho nam nhân viên khi vợ sinh con. Do đó, tôi không thể trả lời câu hỏi này.

Reference:

> Nam nhân viên được nghỉ 5 ngày làm việc liên tục khi vợ sinh con, không trừ vào phép năm.

Contexts đã retrieve/rerank:

```json
[
  "[source: nghi_om.md | title: Chính sách nghỉ ốm | version: 1.0 | effective_date: 01/01/2024]\n nhận đủ 100% lương cơ bản.\n\n## Nghỉ ốm dài hạn\nTrường hợp nghỉ ốm trên 30 ngày/năm, nhân viên cần liên hệ phòng Nhân sự để được hướng dẫn chế độ bảo hiểm dài hạn. Công ty có quyền yêu cầu khám sức khỏe tổng quát trước khi nhân viên quay lại làm việc.",
  "[source: nghi_phep_khong_luong.md | title: Chính sách nghỉ phép không lương | version: 1.2 | effective_date: 01/07/2023]\nc điều hành (CEO)**.\n\n## Ảnh hưởng đến phúc lợi\nTrong thời gian nghỉ không lương, nhân viên không được hưởng lương và các khoản phụ cấp. Bảo hiểm y tế vẫn được duy trì nếu nghỉ dưới 14 ngày. Nghỉ trên 14 ngày, nhân viên cần tự đóng phần bảo hiểm của mình.",
  "[source: nghi_phep_nam_v2024.md | title: Chính sách nghỉ phép năm (Phiên bản 2024) | version: 2.0 | effective_date: 01/01/2024]\n/2024 | Phòng ban: Nhân sự\n\n## Số ngày phép năm\nMỗi nhân viên chính thức được hưởng **15 ngày phép năm** có lương, tăng từ 12 ngày so với chính sách năm 2023. Chính sách này thay thế hoàn toàn phiên bản 1.0 ban hành ngày 01/01/2023.\n\n## Thâm niên công tác\n"
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về số ngày nghỉ cho nam nhân viên khi vợ sinh con. Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Nam nhân viên được nghỉ 5 ngày làm việc liên tục khi vợ sinh con, không trừ vào phép năm.». Nguồn trong contexts: nghi_om.md, nghi_phep_khong_luong.md, nghi_phep_nam_v2024.md. Top contexts thiếu nguồn cần đối chiếu nghi_phep_dac_biet.md; chưa có log candidates để tách lỗi search khỏi rerank.

Hướng sửa cần thử: Với câu hỏi «Nam nhân viên được nghỉ bao nhiêu ngày khi vợ sinh con?», kiểm tra candidates trước/sau rerank tại nghi_phep_dac_biet.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.

### Câu 19 — factual

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 1.000000 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Thời gian thử việc tiêu chuẩn và tối đa (dành cho Manager trở lên) là bao nhiêu ngày?

Answer thực tế:

> Context không cung cấp thông tin về thời gian thử việc tiêu chuẩn và tối đa (dành cho Manager trở lên). Do đó, tôi không thể trả lời câu hỏi này.

Reference:

> Thời gian thử việc tiêu chuẩn là 60 ngày. Đối với vị trí Manager trở lên, có thể kéo dài đến 90 ngày.

Contexts đã retrieve/rerank:

```json
[
  "[source: cong_tac_phi.md | title: Chính sách công tác phí | version: 1.5 | effective_date: 01/01/2024]\nngày** (bao gồm ăn uống và di chuyển nội thành)\n- **Khách sạn**: tối đa **1.200.000 VNĐ/đêm**, thanh toán theo hóa đơn thực tế\n- **Vé máy bay**: hạng phổ thông, đặt trước ít nhất 5 ngày. Cấp Manager trở lên được bay hạng thương gia cho chặng trên 2 giờ\n\n",
  "[source: nghi_phep_nam_v2024.md | title: Chính sách nghỉ phép năm (Phiên bản 2024) | version: 2.0 | effective_date: 01/01/2024]\n 5 ngày trở lên cần được trưởng phòng phê duyệt. Phép năm không sử dụng hết có thể chuyển tối đa 5 ngày sang năm sau, hết hạn vào 31/03 năm kế tiếp. Nhân viên cũng có thể yêu cầu thanh toán bằng tiền cho số ngày phép còn lại.",
  "[source: mentor_buddy.md | title: Chương trình Mentor & Buddy | version: 1.0 | effective_date: 01/06/2024]\nhân viên cùng phòng ban, thâm niên từ 6 tháng.\n\n## Quy tắc quan trọng\nMentor và Buddy phải là **hai người khác nhau** để đảm bảo nhân viên mới có nhiều nguồn hỗ trợ đa dạng. Quản lý trực tiếp không được làm Mentor hoặc Buddy.\n\n## Thời gian chương trình\n"
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về thời gian thử việc tiêu chuẩn và tối đa (dành cho Manager trở lên). Do đó, tôi không thể trả lời câu hỏi này.». Reference nêu: «Thời gian thử việc tiêu chuẩn là 60 ngày. Đối với vị trí Manager trở lên, có thể kéo dài đến 90 ngày.». Nguồn trong contexts: cong_tac_phi.md, nghi_phep_nam_v2024.md, mentor_buddy.md. Top contexts thiếu nguồn cần đối chiếu thu_viec.md; chưa có log candidates để tách lỗi search khỏi rerank.

Hướng sửa cần thử: Với câu hỏi «Thời gian thử việc tiêu chuẩn và tối đa (dành cho Manager trở lên) là bao nhiêu ngày?», kiểm tra candidates trước/sau rerank tại thu_viec.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng.

### Câu 43 — adversarial

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 1.000000 | 0.000000 | 0.000000 | 0.000000 |

Câu hỏi: Mật khẩu phải có tối thiểu bao nhiêu ký tự?

Answer thực tế:

> Context không cung cấp thông tin về yêu cầu mật khẩu, vì vậy không thể trả lời câu hỏi này.

Reference:

> Theo v2.0 HIỆN HÀNH: tối thiểu 12 ký tự. Chính sách v1.0 (đã thay thế) yêu cầu 8 ký tự. RAG có thể lấy cả 2 tài liệu — câu trả lời đúng là 12 ký tự.

Contexts đã retrieve/rerank:

```json
[
  "[source: bao_mat_su_co.md | title: Quy trình xử lý sự cố bảo mật | version: 1.1 | effective_date: 01/05/2024]\nảnh báo antivirus tự động → xử lý trong 24 giờ\n\nThông tin chi tiết sự cố được phân loại **Bí mật**; thông tin liên quan mã nguồn core, bí mật thương mại hoặc kế hoạch M&A thuộc **Tối mật** theo chính sách phân loại dữ liệu.",
  "[source: phan_loai_du_lieu.md | title: Chính sách phân loại dữ liệu | version: 1.0 | effective_date: 01/06/2024]\ntrình nội bộ, biên bản họp, danh bạ nhân viên |\n| 3 | **Bí mật** | Dữ liệu khách hàng, hợp đồng, chiến lược kinh doanh |\n| 4 | **Tối mật** | Mã nguồn core, bí mật thương mại, kế hoạch M&A |\n\n## Quy tắc xử lý\n- **Công khai**: chia sẻ tự do, không hạn chế\n",
  "[source: phan_loai_du_lieu.md | title: Chính sách phân loại dữ liệu | version: 1.0 | effective_date: 01/06/2024]\ný\n- **Công khai**: chia sẻ tự do, không hạn chế\n- **Nội bộ**: chỉ chia sẻ nội bộ, không ra ngoài công ty\n- **Bí mật**: mã hóa khi truyền, hạn chế quyền truy cập theo need-to-know\n"
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Context không cung cấp thông tin về yêu cầu mật khẩu, vì vậy không thể trả lời câu hỏi này.». Reference nêu: «Theo v2.0 HIỆN HÀNH: tối thiểu 12 ký tự. Chính sách v1.0 (đã thay thế) yêu cầu 8 ký tự. RAG có thể lấy cả 2 tài liệu — câu trả lời đúng là 12 ký tự.». Nguồn trong contexts: bao_mat_su_co.md, phan_loai_du_lieu.md. Top contexts thiếu nguồn cần đối chiếu mat_khau_v2.md; chưa có log candidates để tách lỗi search khỏi rerank.

Hướng sửa cần thử: Với câu hỏi «Mật khẩu phải có tối thiểu bao nhiêu ký tự?», kiểm tra candidates trước/sau rerank tại mat_khau_v2.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. Giữ cả v1/v2, chọn phiên bản theo thời điểm được hỏi; không xóa policy cũ.

### Câu 32 — multi_hop

| faithfulness | answer_relevancy | context_precision | context_recall |
| --- | --- | --- | --- |
| 0.500000 | 0.000000 | 0.583333 | 0.000000 |

Câu hỏi: Nhân viên mới cấp Manager có thời hạn thử việc 90 ngày, đang trong tháng thứ 3, có BẮT BUỘC tham dự buổi đào tạo nội bộ của phòng ban không? Tại sao?

Answer thực tế:

> Theo chính sách đào tạo nội bộ (phiên bản 1.3, có hiệu lực từ 01/01/2024), không có thông tin cụ thể nào đề cập đến việc nhân viên mới cấp Manager có bắt buộc tham dự buổi đào tạo nội bộ hay không. Tuy nhiên, chính sách này chỉ nêu rõ ngân sách đào tạo cho các khóa học bên ngoài và không quy định về việc tham gia đào tạo nội bộ. Do đó, không thể xác định rõ ràng rằng nhân viên mới cấp Manager có bắt buộc tham dự hay không dựa trên thông tin hiện có.

Reference:

> Có, BẮT BUỘC. Theo chính sách đào tạo nội bộ, nhân viên mới trong 6 tháng đầu phải tham gia tất cả các buổi đào tạo của phòng ban. Nhân viên tháng thứ 3 (đang thử việc) vẫn nằm trong phạm vi 6 tháng đầu.

Contexts đã retrieve/rerank:

```json
[
  "[source: dao_tao_noi_bo.md | title: Chính sách đào tạo nội bộ | version: 1.3 | effective_date: 01/01/2024]\nổi đào tạo của phòng ban.\n\n## Ngân sách đào tạo\nCông ty dành ngân sách đào tạo **5.000.000 VNĐ/người/năm** cho các khóa học bên ngoài. Nhân viên có thể đăng ký khóa học qua hệ thống Learning Portal và cần phê duyệt của trưởng phòng.\n\n## Đánh giá hiệu quả\n",
  "[source: hoan_chi_dao_tao.md | title: Chính sách hoàn chi đào tạo | version: 1.1 | effective_date: 01/07/2023]\ncho nhân viên có **thâm niên từ 1 năm trở lên**. Chi phí được tài trợ tối đa **30.000.000 VNĐ/khóa** và cần phê duyệt của Giám đốc phòng ban.\n\n## Cam kết hoàn chi\n",
  "[source: mentor_buddy.md | title: Chương trình Mentor & Buddy | version: 1.0 | effective_date: 01/06/2024]\nhân viên cùng phòng ban, thâm niên từ 6 tháng.\n\n## Quy tắc quan trọng\nMentor và Buddy phải là **hai người khác nhau** để đảm bảo nhân viên mới có nhiều nguồn hỗ trợ đa dạng. Quản lý trực tiếp không được làm Mentor hoặc Buddy.\n\n## Thời gian chương trình\n"
]
```

Đối chiếu nội dung (Task 3): Answer chưa trả lời được yêu cầu: «Theo chính sách đào tạo nội bộ (phiên bản 1.3, có hiệu lực từ 01/01/2024), không có thông tin cụ thể nào đề cập đến việc nhân viên mới cấp Manager có bắt buộc t». Reference nêu: «Có, BẮT BUỘC. Theo chính sách đào tạo nội bộ, nhân viên mới trong 6 tháng đầu phải tham gia tất cả các buổi đào tạo của phòng ban. Nhân viên tháng thứ 3 (đang thử việc) vẫn nằm trong phạm vi 6 tháng đầu.». Nguồn trong contexts: dao_tao_noi_bo.md, hoan_chi_dao_tao.md, mentor_buddy.md. Đã lấy đúng tên file nhưng answer chưa đáp ứng; kiểm tra passage thiếu điều kiện hay generation bỏ sót căn cứ. Metadata source không chứng minh passage đã trả lời được câu hỏi. Context đào tạo thiếu nguyên câu quy định nhân viên mới trong 6 tháng đầu.

Hướng sửa cần thử: Với câu hỏi «Nhân viên mới cấp Manager có thời hạn thử việc 90 ngày, đang trong tháng thứ 3, có BẮT BUỘC tham dự buổi đào tạo nội bộ của phòng ban không? Tại sao?», kiểm tra candidates trước/sau rerank tại dao_tao_noi_bo.md; thử mở rộng parent/mục để giữ nguyên điều kiện, rồi sinh/chấm lại trên một batch riêng. Thu đủ từng căn cứ trước khi cộng số ngày hoặc suy điều kiện áp dụng.

## Matrix và nhóm yếu nhất

| Worst metric | factual | multi_hop | adversarial |
| --- | --- | --- | --- |
| faithfulness | 1 | 4 | 0 |
| context_recall | 0 | 5 | 0 |
| context_precision | 1 | 3 | 0 |
| answer_relevancy | 18 | 8 | 10 |

Nhóm yếu nhất theo mean: **multi_hop**, 0.516140. Worst metric thường gặp nhất: **answer_relevancy**. Tổng cột 20/20/10 là kích thước mẫu, không đo chất lượng; mọi câu được đếm một lần.

## Bẫy adversarial, cải tiến và giới hạn

Adversarial mean 0.540863, factual mean 0.558209; điều kiện adversarial < factual: True. Corpus giữ nghỉ phép 2023/2024 và mật khẩu v1/v2. Đối chiếu số ngày phép, độ dài/chu kỳ mật khẩu và các phủ định trong evidence ở trên; điểm thấp hơn không tự chứng minh hệ thống nhận ra xung đột phiên bản.

Ưu tiên thử chunk theo mục để giữ trọn điều kiện thay vì cắt giữa câu; thêm version/effective-date metadata filtering theo thời điểm được hỏi mà vẫn giữ tài liệu lịch sử; thử top-k lớn hơn cho multi-hop rồi rerank và deduplicate. Đổi từng yếu tố một, sinh lại answers và chạy RAGAS để so từng ID, không sửa test set. 50 câu và một lượt model chưa đủ suy rộng sang production; RAGAS cũng có sai số judge.

## Đọc lỗi từ evidence của batch này

- **IDs 1/8/9/26 — thiếu chính sách nghỉ đặc biệt.** Ba contexts của mỗi câu không có `nghi_phep_dac_biet.md`. File gốc ghi kết hôn 3 ngày, tang lễ 3 ngày, nam có vợ sinh con 5 ngày và con kết hôn 1 ngày. Answer đều nói thiếu thông tin. Đây là bằng chứng thiếu căn cứ ở top contexts, chưa đủ tách lỗi search/rerank. Cần trace vị trí các chunks này trước/sau rerank, thay vì chỉ đổi prompt. Với ID 26, reference cộng 3+1=4; câu 'phép đặc biệt không cộng dồn' ở cuối corpus cần người quản lý policy làm rõ phạm vi áp dụng khi mở rộng đánh giá. Giữ reference được cấp cho lượt chấm hiện tại.
- **ID 6 — thiếu cầu nối giữa lương và phân loại.** Context 1 có bảng cấp 3 Bí mật, nhưng không có câu 'Thông tin lương là dữ liệu Bí mật' trong `ky_luong.md`. Chỉ bảng phân loại chưa xác định lương ở cấp nào. Faithfulness thấp không tự chứng minh answer đã bịa cấp độ; answer thực tế từ chối xác định. Hướng sửa là lấy cả quy chế lương và quy tắc xử lý dữ liệu, rồi đối chiếu từng khẳng định.
- **ID 16 — nhầm loại đoạn VPN.** Context 1 nói ngắt phiên sau 12 giờ; điều cần hỏi là khóa tài khoản sau 60 ngày không hoạt động trong cùng file. Hai contexts còn lại về tạm ứng/mật khẩu cũ không bù được đoạn thiếu. Thử mở rộng parent hoặc retrieve theo mục quản lý tài khoản.
- **ID 19 — thiếu hẳn nguồn thời gian thử việc.** Contexts là công tác phí, phép năm và Mentor/Buddy; không có `thu_viec.md` với 60 ngày tiêu chuẩn/90 ngày cho Manager. Không thể khắc phục chỉ bằng yêu cầu LLM trả lời chắc hơn khi passage chưa được lấy.
- **ID 32 — mất đầu điều kiện trong chunk.** Context 1 bắt đầu 'ổi đào tạo của phòng ban' rồi chuyển sang ngân sách; câu đầy đủ ở `dao_tao_noi_bo.md` quy định nhân viên mới trong 6 tháng đầu bắt buộc tham gia. Child chunk theo ký tự làm mất điều kiện này; đây là ví dụ cụ thể cho thử parent expansion/chunk theo mục. Answer còn suy từ phần ngân sách thành kết luận policy không quy định đào tạo nội bộ; cần giới hạn phát biểu ở contexts đã thấy, thay vì khẳng định về toàn bộ tài liệu.
- **ID 43 — thiếu retrieval trước khi kiểm tra version.** Top contexts không có `mat_khau_v1.md` hoặc `mat_khau_v2.md`, nên lượt này chưa chứng minh LLM chọn nhầm 8 thay vì 12 ký tự; answer đã không đưa ra con số. Sau khi lấy được đúng passage, mới kiểm tra ưu tiên v2 hiện hành mà vẫn giữ v1 để trả lời câu lịch sử.
- **ID 48 — thiếu exclusion PVI.** Contexts lấy gói gia đình, bồi hoàn và nghỉ ốm. Điều 'thử việc chưa được hưởng gói PVI' nằm trong `thu_viec.md`, không được lấy. Answer từ chối, không phải trả lời sai rằng thử việc được PVI; cần phân biệt thiếu căn cứ phủ định với đảo phủ định.

**Đối chiếu bẫy ngoài bottom 10:** ID 44 có cả v1/v2 trong contexts và answer chọn 120 ngày theo v2; đây là một lần xử lý xung đột phiên bản thành công. IDs 41/42 chọn 15 ngày và quy tắc 3 năm theo bản 2024. ID 45 trả lời MFA bắt buộc, ID 47 giữ phủ định không tự xử lý malware. Ngược lại, ID 49 đã lấy cả hai phiên bản phép nhưng answer bỏ số 12 ngày của bản 2023; IDs 46/50 chưa trả lời được phủ định/cấm mà reference yêu cầu. Vì vậy adversarial mean thấp hơn factual chỉ là mô tả batch, không chứng nhận mọi bẫy đã được giải quyết.

**Thứ tự cải tiến:** trace search/rerank cho nhóm nghỉ đặc biệt và thử việc; thử parent expansion/chunk theo heading cho VPN và đào tạo; bổ sung retrieval nhiều nguồn cho lương/PVI; sau đó đánh giá version filtering trên cả câu hiện hành và lịch sử. Đo từng thay đổi bằng batch mới có nguồn riêng; batch hiện tại vẫn là baseline.
