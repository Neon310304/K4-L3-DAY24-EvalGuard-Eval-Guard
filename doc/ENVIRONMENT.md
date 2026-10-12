# Môi trường K4 Track 3A

## Phiên bản mục tiêu và cách kiểm tra

Dùng Python 3.11 cho lab này. Tạo virtualenv mới sau khi tải starter, cài
dependencies và chạy `pip check` trên máy của nhóm. Tests hỗ trợ chạy không
cần API hay model; student tests vẫn fail nếu các hàm TODO chưa được làm.

Bộ phiên bản lõi trong starter: RAGAS 0.1.22; LangChain 0.2.17; langchain-core
0.2.43; community 0.2.19; openai integration 0.1.25; OpenAI SDK 1.109.1; NeMo
0.10.0; Annoy 1.17.3; NumPy 1.26.4. Các pins nằm trong `requirements/constraints-core.txt`.
Đây là constraints cho tập lõi, **không phải lock toàn bộ dependencies**.

Trên Windows, build `annoy==1.17.3` cần Microsoft Visual C++ 14.0 trở lên.
Sau khi cài compiler, nhóm chạy các bước kiểm chứng phía dưới trên chính môi
trường sẽ làm lab. Kết quả unit tests hoặc pip resolve không chứng minh full
NeMo đã cài/chạy được.

Theo [README của NeMo v0.10.0](https://github.com/NVIDIA/NeMo-Guardrails/blob/v0.10.0/README.md),
bản này hỗ trợ Python đến 3.11 và cần compiler/dev tools cho Annoy. Không lấy
hướng dẫn bản NeMo mới nhất để suy ra bản 0.10.0 hỗ trợ Python 3.12+.

## Chuẩn bị compiler và virtualenv trước buổi học

Trên Windows, cài Microsoft C++ Build Tools, chọn workload **Desktop development
with C++**, bao gồm MSVC và Windows SDK. Mở lại terminal sau cài; dùng Developer
PowerShell nếu compiler chưa có trong PATH. Làm theo
[hướng dẫn Microsoft](https://learn.microsoft.com/en-us/cpp/build/vscpp-step-0-installation?view=msvc-170).
Việc cài compiler/tải model không thuộc 15 phút kiểm tra đầu buổi.

Từ gốc repo trên PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements/requirements.txt -c requirements/constraints-core.txt
.\.venv\Scripts\python.exe -m pip check
```

Không bắt buộc kích hoạt virtualenv: dùng đường dẫn interpreter như trên.
Nếu muốn chạy `Activate.ps1` và gặp lỗi execution policy, có thể cho phép script
chỉ trong phiên PowerShell hiện tại rồi kích hoạt:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Nếu policy của tổ chức vẫn chặn, dùng interpreter trực tiếp; không thay policy
toàn máy. Xem [hướng dẫn venv Python 3.11](https://docs.python.org/3.11/library/venv.html).
macOS/Linux dùng `python3.11 -m venv .venv` và `source .venv/bin/activate`;
cần toolchain C++ của hệ điều hành khi build Annoy.

## Kiểm chứng cài đặt và tải model

Cài thành công qua pip chưa chứng minh đã tải model hoặc API kết nối được.
Kiểm tra các lớp riêng biệt để biết lỗi nằm ở đâu:

```bash
python -m pip check
python -c "import ragas, nemoguardrails, presidio_analyzer, spacy; print('imports OK')"
python -m spacy download en_core_web_lg
docker compose -f infra/docker-compose.yml up -d
python scripts/setup_answers.py --live
```

Qdrant dùng tag [v1.9.7](https://github.com/qdrant/qdrant/releases/tag/v1.9.7),
không dùng `latest`. Setup sẽ tải embedding BGE-M3/reranker theo module bài
trước; nhóm cần cache/download xong trước lớp. Model/download/indexing có thể
mất lâu tùy máy và mạng. Generation/enrichment có thể gọi API, có chi phí.

Ghi OS, Python, kết quả pip/import/compiler/model download trong TEAM. Nếu full
stack cài chưa xong, ghi lỗi thật; không điền “tương thích” dựa trên dry-run.

## Full runtime trong Docker trên Windows

Nếu chưa có MSVC, image Linux Python 3.11 dùng GCC/build-essential để build Annoy.
Model cache được giữ trong volume; API key đọc từ `.env` được Git ignore.
Constraints pin PyArrow 17.0.0/NumPy 1.26.4 để tránh lỗi ABI mà `pip check` có thể
không phát hiện. Dockerfile kiểm tra cả dependency metadata và imports thực tế.

```powershell
docker compose -f infra/docker-compose.yml --profile runtime build lab
docker compose -f infra/docker-compose.yml up -d qdrant
docker compose -f infra/docker-compose.yml run --rm lab python -m pip check
docker compose -f infra/docker-compose.yml run --rm lab python scripts/verify_runtime.py
docker compose -f infra/docker-compose.yml run --rm lab python scripts/setup_answers.py --live
```

Dockerfile pin `en_core_web_lg` 3.8.0 và SHA256 của wheel chính thức. Khi đã có
wheel đúng hash trong cache, có thể dùng build arg `SPACY_MODEL_URL` để cài lại
từ bản cache; không commit wheel/cache vào repo.

Sau khi setup đã cache model, kiểm tra pipeline mà không sinh answers mới:

```powershell
docker compose -f infra/docker-compose.yml run --rm -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 lab python scripts/verify_runtime.py --with-pipeline
```

Tùy chọn `--with-pipeline` **tạo lại collection lab24_production**, rồi thử
search/rerank và kiểm tra source/parent metadata. Lệnh không gọi generation hay
API chấm điểm; dùng models BGE-M3/FlashRank đã cache. Không dùng chế độ offline
khi chưa tải model xong.

## Tạo môi trường unit test offline

Khi chỉ sửa logic/scaffold, không cần cài NeMo, ML model hoặc C++ compiler.
Tạo môi trường riêng với các dependencies đã pin:

```powershell
py -3.11 -m venv .venv-tests
.\.venv-tests\Scripts\python.exe -m pip install -r requirements/requirements-test.lock.txt
.\.venv-tests\Scripts\python.exe -m pip check
.\.venv-tests\Scripts\python.exe -m pytest tests/ -m support -q
```

`requirements/requirements-test.txt` ghi dependencies trực tiếp; file `.lock.txt` khóa
toàn bộ dependencies của tập test. Đây chỉ là lock unit test, không thay constraints hoặc
cài đặt full runtime. Không commit virtualenv, key hoặc cache model.

## Phục hồi Docker khi WSL không phản hồi

Nếu Docker báo `DockerDesktop/Wsl/CommandTimedOut` và cả `wsl --list --verbose`
cũng treo, đóng Docker rồi chạy lệnh sau trong PowerShell **Administrator**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/repair_wsl.ps1
```

Script dừng các tiến trình Docker/WSL đang kẹt, khởi động lại WslService và kiểm
tra WSL với timeout; giữ images, volumes và VHD. Log ở `.cache/wsl-repair/`.
Việc restart dịch vụ sẽ dừng các phiên WSL và containers đang chạy. Khi WSL phản
hồi, mở Docker bình thường rồi kiểm tra:

```powershell
docker desktop start --detach
docker info
docker compose -f infra/docker-compose.yml up -d qdrant
```

Runtime guard Windows có thể chọn model đã cài bằng `PRESIDIO_SPACY_MODEL`.
Batch C trong TEAM dùng `en_core_web_sm`; Docker mặc định `en_core_web_lg`.
Registry guard chỉ giữ email/phone và pattern VN. Không suy giảm/tăng chất lượng
hoặc latency chỉ từ đổi model; cần chạy lại cùng protocol để so sánh.
