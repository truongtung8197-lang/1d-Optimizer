# ARCHITECTURE

## Cấu trúc thư mục

```
steel_cutting_optimizer/
├── main.py                 # orchestrator, CLI entry point
├── config.py               # CẤU HÌNH TẬP TRUNG — chỉnh rule tại đây
├── excel_style.py          # định dạng Excel dùng chung (màu, đậm, căn lề, freeze)
├── create_input_excel.py   # sinh data/input.xlsx (2 sheet Stock+Required) có định dạng
├── input_loader.py         # đọc + validate input (Excel hoặc CSV)
├── join_patterns.py        # sinh cặp (a,b) hợp lệ cho mỗi cấu kiện
├── cutting_engine.py       # FFD + remnant pool, gán đoạn vào cây stock
├── optimizer.py            # greedy ngẫu nhiên + restart, cải thiện lời giải
├── report_generator.py     # xuất kết quả ra Excel/JSON, kèm % sử dụng
├── models.py               # dataclass: Stock, Component, Segment, CutPlan
├── run_demo.py             # chạy nhanh demo với data mặc định
├── data/
│   ├── input.xlsx          # INPUT CHÍNH: sheet "Stock" + sheet "Required"
│   ├── stock.csv           # (tùy chọn, tương thích cũ)
│   └── required.csv        # (tùy chọn, tương thích cũ)
└── output/
    ├── cutting_plan.json
    └── cutting_plan.xlsx
```

## Luồng dữ liệu

```
data/input.xlsx (sheet Stock + Required)
        │
        ▼
  input_loader.py  → List[Stock], List[Component]   (load_from_excel)
        │
        ▼
 join_patterns.py  → với mỗi Component: List[(a, b)] hợp lệ
                      (đọc rule đoạn tối thiểu từ config.py)
        │
        ▼
 cutting_engine.py → chọn 1 pattern (a,b) mỗi Component,
                      gán đoạn a, b vào các cây Stock/remnant
                      (FFD + remnant pool)
        │
        ▼
   optimizer.py     → greedy ngẫu nhiên + restart, giữ lời giải tốt nhất
                      (ít cây trước, rồi ít tổng phế liệu)
        │
        ▼
report_generator.py → xuất cutting_plan.json / .xlsx
                      (thêm % sử dụng, định dạng màu qua excel_style.py)
        │
        ▼
   main.py          → in tóm tắt + ví dụ ra console,
                      tự mở file Excel sau khi chạy (cờ --no-open để tắt)
```

## Models (models.py) — dataclass chính

- `Stock`: id, length, quantity
- `Component`: id, length, quantity
- `Segment`: length, source ("stock" | "remnant"), parent_stock_id, role ("a"|"b")
- `CutPlan`: stock_id, segments_cut: List[Segment], remnant_length
- `ComponentAssembly`: component_id, segment_a, segment_b, source_stock_ids

## Cấu hình (config.py)

Tất cả rule có thể chỉnh tại `config.py` (không cần đụng logic code):

- `MIN_SEGMENT_MODE`: `"ratio"` (đoạn ≥ L × ratio) hoặc `"fixed"` (đoạn ≥ mm cố định).
- `MIN_SEGMENT_RATIO`: tỷ lệ tối thiểu (mặc định 1/3).
- `MIN_SEGMENT_FIXED_MM`: độ dài tối thiểu cố định (dùng khi mode `"fixed"`).
- `STEP_MM`: bước rời rạc hóa pattern (mặc định 20mm, có thể chỉnh theo dung sai).
- `MIN_USABLE_REMNANT_MM`: ngưỡng remnant tái dùng (mặc định 200mm).
- `MAX_RESTARTS`: số lần restart optimizer (mặc định 60/100).

## Định dạng Excel (excel_style.py)

Module dùng chung cho input.xlsx và cutting_plan.xlsx:

- Header nền xanh đậm + chữ trắng in đậm.
- Banded rows (màu xen kẽ dòng).
- Freeze pane + auto filter.
- Tô hồng dòng phế liệu (Cutting Detail).
- Tự chỉnh độ rộng cột, thêm viền.

## Nguyên tắc thiết kế (theo phong cách làm việc đã biết)

- Mỗi file 1 trách nhiệm rõ ràng (single responsibility).
- Business logic (cutting_engine, join_patterns, optimizer) tách biệt hoàn toàn
  khỏi I/O (input_loader, report_generator).
- Không over-engineer: bắt đầu bằng greedy đơn giản (Phase 0-3), chỉ thêm
  optimizer.py nếu kết quả greedy chưa đủ tốt.
- File log dạng text/JSON để debug từng bước cắt (đặc biệt hữu ích khi review
  bằng tay trước khi thi công thực tế).

## Ghi chú phạm vi hiện tại

- Hỗ trợ **1 loại stock_length** (theo quyết định phạm vi). Nếu gặp nhiều loại,
  `run_cutting` / `run_cutting_optimized` báo `ValueError` và dừng lại hỏi
  thay vì tự quyết định.
- Optimizer mặc định chạy `config.MAX_RESTARTS` lần (có thể ghi đè bằng cờ
  `--restarts`), giữ lời giải tốt nhất theo tiêu chí (số cây, tổng phế liệu).
- Các rule kỹ thuật (đoạn tối thiểu, bước rời rạc hóa, ngưỡng remnant) tập
  trung tại `config.py`.
- Input chính là **`data/input.xlsx`** (2 sheet). Vẫn hỗ trợ CSV `--stock`/`--required`
  để tương thích ngược.
