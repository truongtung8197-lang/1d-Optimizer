# PROJECT BRIEF — Công cụ tối ưu cắt & nối thép hình/thanh

## Bài toán

Tối ưu việc cắt thép nguyên liệu (stock) thành các đoạn, nối lại thành cấu kiện,
sao cho: dùng ít cây thép nhất, phế liệu ít nhất, và tuân thủ ràng buộc kỹ thuật
về mối nối.

Bản chất: **1D Cutting Stock Problem + Remnant Reuse + Fixed Splicing Constraint**.

## Input

- **Stock** + **Required**: nằm chung trong **1 file Excel `data/input.xlsx`**
  với 2 sheet "Stock" và "Required" (không phải mở nhiều file). Có định dạng sẵn
  (header màu, freeze, filter). Vẫn hỗ trợ 2 file CSV cũ (`--stock`/`--required`)
  để tương thích ngược.
- **Stock**: thép nguyên liệu, chiều dài cố định (vd 6000 mm), số lượng nhiều cây,
  có thể nhiều loại chiều dài stock khác nhau.
- **Required**: danh sách cấu kiện cần chế tạo, mỗi cấu kiện có chiều dài (có thể
  dài hơn 1 cây stock) và số lượng cần.

## Ràng buộc bắt buộc (CORE RULE — không thay đổi)
>
> **Mọi cấu kiện luôn được tạo từ đúng 2 đoạn thép nối với nhau bằng 1 tăng đơ ở giữa.
> Không có trường hợp 1 đoạn (nguyên cây) hay 3 đoạn trở lên.**

Với mỗi cấu kiện chiều dài `L`, cắt thành 2 đoạn `a + b = L` sao cho:

- `a ≥ L/3` và `b ≥ L/3` (ràng buộc chịu lực — đoạn ngắn nhất ≥ 1/3 tổng chiều dài)
- `a ≤ stock_length` và `b ≤ stock_length` (mỗi đoạn phải cắt được từ 1 cây nguyên liệu)

Ví dụ cấu kiện 7500 mm, stock 6000 mm:

- `6000 + 1500` → ❌ không hợp lệ (1500 < 2500)
- `5000 + 2500` → ✅ hợp lệ
- `4500 + 3000` → ✅ hợp lệ

## Mục tiêu tối ưu

Tối ưu **toàn cục** trên toàn bộ danh sách cấu kiện (không tối ưu từng cấu kiện
riêng lẻ):

1. Giảm thiểu số cây thép nguyên liệu sử dụng.
2. Giảm thiểu tổng phế liệu (chiều dài dư không dùng được).
3. Phần dư sau khi cắt 1 cây (remnant) phải được xét dùng lại cho đoạn khác
   trước khi mở cây mới.

## Output mong muốn

- Cây nào cắt thành đoạn nào, dư bao nhiêu.
- Đoạn nào nối với đoạn nào (cặp a-b) qua tăng đơ, tạo thành cấu kiện nào.
- Tổng số cây nguyên liệu dùng.
- **% sử dụng** (tổng chiều dài dùng ÷ tổng stock đã dùng).
- Tổng chiều dài/khối lượng phế liệu.
- Phương án cắt/nối chi tiết, export Excel (đã format màu, đậm, căn lề) + JSON.

## Đối tượng thực thi

AI coding agent **Cline** (model DeepSeek V4 Flash, free, context 1M token).
Code Python, ưu tiên đơn giản, module hoá rõ ràng, dễ debug từng phase.

## Trạng thái triển khai (đã hoàn tất)

- **Phase 0-3**: input, join pattern, cutting engine (FFD + remnant pool),
  report generator (JSON + Excel 4 sheet) — đã chạy end-to-end.
- **Phase 4 (Optimizer)**: greedy ngẫu nhiên + restart, chọn join pattern theo
  phế ước lượng, giữ lời giải tốt nhất (ít cây trước, rồi ít phế liệu).
  - Kết quả trên bộ dữ liệu thực tế: **31 cây → 29 cây**, phế **37,436mm → 24,793mm**.
- **Phase 5 (CLI)**: `main.py` chạy 1 lệnh, **tự mở file Excel** sau khi chạy
  (cờ `--no-open` để tắt); `run_demo.py` chạy nhanh với data mặc định.
- **Giao diện Excel**: input gộp vào `data/input.xlsx` (2 sheet); output được
  format màu (header, banded rows, highlight phế liệu, freeze, filter); Summary
  thêm **% sử dụng**. JSON có `used_percent`.
- Phạm vi hiện tại: hỗ trợ **1 loại stock_length**; gặp nhiều loại → dừng hỏi.

## Cấu hình rule (config.py)

Tất cả rule kỹ thuật tập trung tại `config.py`, chỉ cần sửa file này không cần
đụng logic code:

- **Đoạn tối thiểu**: `MIN_SEGMENT_MODE = "ratio"` (đoạn ≥ L × `MIN_SEGMENT_RATIO`,
  mặc định 1/3) hoặc `"fixed"` (đoạn ≥ `MIN_SEGMENT_FIXED_MM`, vd 2000mm).
- **Bước rời rạc hóa**: `STEP_MM` (mặc định 50mm).
- **Ngưỡng remnant tái dùng**: `MIN_USABLE_REMNANT_MM` (mặc định 200mm).
- **Số lần restart optimizer**: `MAX_RESTARTS` (mặc định 60).
