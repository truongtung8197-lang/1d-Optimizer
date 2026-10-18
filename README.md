# 1d-Optimizer — Tối ưu cắt & nối thép hình

Công cụ tính toán cắt thép nguyên liệu thành các đoạn, nối thành cấu kiện sao
cho **dùng ít cây nhất, phế liệu ít nhất**, tuân thủ ràng buột kỹ thuật mối nối.

**Bài toán:** 1D Cutting Stock + Remnant Reuse + Fixed Splicing Constraint.

## Core rule

- Mỗi cấu kiện (chiều dài `L`) = **đúng 2 đoạn** `a + b = L`, nối bằng **1
  tăng đơ**.
- Đoạn ngắn nhất `≥ L/3` (có thể đổi trong `config.py`).
- Mỗi đoạn phải `≤ chiều dài stock` để cắt được từ 1 cây.

## Cấu trúc

```
steel_cutting_optimizer/
├── main.py                  # CLI — chạy toàn bộ pipeline
├── config.py                # CẤU HÌNH tập trung (rule kỹ thuật)
├── run_demo.py              # Chạy nhanh với data mặc định
├── create_input_excel.py    # Tạo lại data/input.xlsx
├── input_loader.py          # Đọc Excel (2 sheet) hoặc CSV
├── join_patterns.py         # Sinh cặp (a, b) hợp lệ
├── cutting_engine.py        # FFD + remnant pool
├── optimizer.py             # Greedy ngẫu nhiên + restart
├── report_generator.py      # Xuất JSON + Excel
├── models.py                # Dataclass (Stock, Component, …)
├── excel_style.py           # Format màu Excel chung
├── data/input.xlsx          # INPUT (2 sheet: Stock + Required)
└── output/                  # cutting_plan.json + cutting_plan.xlsx
```

Các file tài liệu chi tiết: `PROJECT_BRIEF.md`, `ALGORITHM.md`,
`ARCHITECTURE.md`, `DATA_SCHEMA.md`, `TASKS.md`.

## Cài đặt

Yêu cầu: Python 3.10+. Chỉ cần 1 thư viện bên ngoài:

```bash
pip install openpyxl
```

## Hướng dẫn sử dụng

> **Chạy từ thư mục `steel_cutting_optimizer/`.** Tất cả lệnh bên dưới đều
> thực thi từ thư mục này.

### 1. Chuẩn bị dữ liệu

Dữ liệu nằm trong **`data/input.xlsx`** — 1 file Excel gồm 2 sheet:

**`Stock`** (thép nguyên liệu):

| stock_type_id | length_mm | quantity |
|---|---|---|
| S6000 | 6000 | 500 |

**`Required`** (cấu kiện cần làm):

| component_id | length_mm | quantity |
| --- | --- | --- |
| fc344 | 2066 | 2 |
| fc83 | 7065 | 3 |
| … | … | … |

Cách tạo lại file Excel mẫu (có sẵn dữ liệu thực):

```bash
python create_input_excel.py
```

Sau khi có `input.xlsx`, mở ra và **chỉnh sửa trực tiếp** 2 sheet Stock và
Required — thay thế bằng số liệu thực tế của bạn. Lưu lại và chạy là xong,
không cần mở thêm file nào khác.

> **Hỗ trợ ngược ngẵa (cũ):** nếu chưa có file Excel, có thể dùng 2 file CSV
> riêng `data/stock.csv` và `data/required.csv`. Cách bố trí cột tương tự như
> trên.

### 2. Chạy chính (khuyên dùng)

```bash
python main.py
```

Lệnh này thực hiện toàn bộ pipeline:

1. Đọc `data/input.xlsx` (mặc định).
2. Sinh join patterns cho từng cấu kiện.
3. Chạy optimizer (greedy ngẫu nhiên + restart, mặc định `MAX_RESTARTS = 500`
   lần — lấy từ `config.py`).
4. Xuất kết quả ra `output/cutting_plan.json` + `output/cutting_plan.xlsx`.
5. In tóm tắt ra console: số cây dùng, % sử dụng, tổng phế liệu, ví dụ cây cắt,
   ví dụ cấu kiện nối, danh sách cảnh báo.
6. **Tự động mở file Excel** kết quả (trên Windows dùng `os.startfile`, trên
   macOS/Linux dùng `open`/`xdg-open`).

### 3. Các cờ (flag) dùng với `main.py`

| Cờ | Mô tả | Mặc định |
| --- | --- | --- |
| `--input <file>` | Đường dẫn file Excel input (2 sheet Stock+Required) | `data/input.xlsx` |
| `--stock <file>` | Đường dẫn file CSV stock (tùy chọn, dùng khi không có Excel) | `None` |
| `--required <file>` | Đường dẫn file CSV required (tùy chọn) | `None` |
| `--out <folder>` | Thư mục lưu kết quả xuất | `output` |
| `--restarts <N>` | Số lần chạy lại optimizer (ghi đè `config.MAX_RESTARTS`) | Lấy từ `config.py` |
| `--no-open` | Không tự mở file Excel sau khi chạy xong | (mở tự động) |

**Quy tắc chọn nguồn input:**

- Nếu **không truyền** `--stock` và `--required` → đọc từ `--input` (file
  Excel gộp 2 sheet).
- Nếu truyền cả 2 tham số `--stock` + `--required` → đọc từ 2 file CSV
  (bỏ qua `--input`).

#### Ví dụ dòng lệnh thực tế

```bash
# Chạy thường lệ với Excel mặc định — mở luôn file kết quả
python main.py

# Chạy với CSV (backward compat) — bỏ qua input.xlsx
python main.py --stock data/stock.csv --required data/required.csv

# Chạy nhưng không tự động mở Excel
python main.py --no-open

# Tăng số lần tối ưu để kết quả tốt hơn (chậm hơn, dùng cho bộ lớn)
python main.py --restarts 1000

# Dùng file Excel khác và xuất ra thư mục khác
python main.py --input data/input_khac.xlsx --out output/ket_qua

# Dùng CSV + tắt mở file + giới hạn số restart
python main.py --stock data/stock.csv --required data/required.csv --no-open --restarts 50
```

### 4. Chạy demo nhanh

`run_demo.py` là wrapper ngắn gọn của `main.py` — tự động truyền `--out
output` và chuyển tiếp mọi cờ bạn gõ vào:

```bash
python run_demo.py
```

Tương đương với:

```bash
python main.py --out output
```

Hỗ trợ truyền thẳng cờ cho `main.py`:

```bash
python run_demo.py --no-open           # chạy không mở Excel
python run_demo.py --restarts 200      # tăng số vòng tối ưu
python run_demo.py --input data/khac.xlsx   # dùng file Excel khác
```

### 5. Điều chỉnh rule kỹ thuật (chỉ sửa `config.py`, không sờ code)

Tất cả rule nằm ở **`config.py`**. Mở file, sửa giá trị, lưu lại, chạy lại là
áp dụng ngay:

```python
MIN_SEGMENT_MODE = "ratio"        # "ratio" → dùng tỷ lệ; "fixed" → dùng mm cố định
MIN_SEGMENT_RATIO = 3 / 10        # dùng khi mode="ratio": đoạn ngắn nhất ≥ L × 0.3
MIN_SEGMENT_FIXED_MM = 2000.0     # dùng khi mode="fixed": đoạn ngắn nhất ≥ 2000mm
STEP_MM = 100.0                   # bước rời rạc hóa pattern (dung sai cắt thực tế)
MIN_USABLE_REMNANT_MM = 200.0     # phần dư ≥ 200mm mới được giữ lại tái dùng
MAX_RESTARTS = 500                # số lần restart optimizer (tăng → tốt hơn nhưng chậm)
```

Ví dụ: muốn đổi ràng buộc từ `L/3` sang `L/4`, thay `MIN_SEGMENT_RATIO` từ
`3/10` thành `1/4`. Muốn đoạn tối thiểu cố định 2500mm, đổi `MIN_SEGMENT_MODE`
thành `"fixed"` và `MIN_SEGMENT_FIXED_MM` thành `2500.0`.

### 6. Kết quả xuất ra

**JSON** — `output/cutting_plan.json`:

- `summary`: số cây dùng, tổng stock (mm), tổng sử dụng (mm), `% sử dụng`,
  phế liệu theo loại stock.
- `cuts`: chi tiết mỗi cây cắt thành đoạn nào, dư bao nhiêu, phần dư được tái
  dùng cho cấu kiện nào.
- `assemblies`: mỗi cấu kiện = 2 đoạn a + b nối bằng tăng đơ.
- `warnings`: danh sách cảnh báo (cấu kiện vô nghiệm, thiếu stock…).

**Excel** — `output/cutting_plan.xlsx` (4 sheet, format màu):

1. **Summary**: tổng cây dùng, % sử dụng, phế liệu theo loại.
2. **Cutting Detail**: từng đoạn cắt từ cây nào, dòng phế liệu tô hồng.
3. **Assembly Detail**: mỗi cấu kiện — đoạn a (nguồn), đoạn b (nguồn), nối
   tăng đơ.
4. **Warnings** (nếu có).

## Chạy test

```bash
python -m unittest test_join_patterns.py test_cutting_engine.py test_load.py
```

## Kết quả trên bộ dữ liệu mẫu

| Phương pháp | Số cây | Phế liệu |
| --- | --- | --- |
| Greedy đơn giản | 31 | 37,436 mm |
| Optimizer | 29 | 24,793 mm |

~34% giảm phế liệu, giảm 2 cây so với greedy cũ.

## Phạm vi hiện tại & hạn chế

- Hỗ trợ **1 loại `stock_length`** duy nhất. Nếu input có nhiều loại chiều
  dài khác nhau, chương trình sẽ dừng và báo lỗi — cần xác nhận chiến lược
  mới.
