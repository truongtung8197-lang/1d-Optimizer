# TASKS — Checklist thực thi cho Cline

Đọc `PROJECT_BRIEF.md`, `ARCHITECTURE.md`, `ALGORITHM.md`, `DATA_SCHEMA.md`
trước khi bắt đầu. Làm theo đúng thứ tự phase, mỗi phase xong phải test trước
khi sang phase tiếp.

## Phase 0 — Setup + Input

- [x] Tạo cấu trúc thư mục theo `ARCHITECTURE.md`
- [x] `models.py`: dataclass Stock, Component, Segment, CutPlan, ComponentAssembly
- [x] `input_loader.py`: đọc + validate input (Excel 2 sheet hoặc CSV)
- [x] **Gộp input vào `data/input.xlsx`** (2 sheet Stock + Required) — không phải mở nhiều file

## Phase 1 — Join Pattern Generator

- [x] `join_patterns.py`: hàm `generate_2seg_patterns(L, stock_length, step)`, đọc rule từ config
- [x] Test theo config động (ratio hoặc fixed): L=7500, L=8200, case vô nghiệm

## Phase 2 — Cutting Engine (core, quan trọng nhất)

- [x] `cutting_engine.py`: implement FFD + remnant pool theo `ALGORITHM.md` mục 2
- [x] Validate: mỗi cây cắt ra tổng đúng bằng stock_length, mỗi cấu kiện đủ 2 đoạn ≥ min rule, không đoạn nào dùng trùng

## Phase 3 — Report Generator

- [x] `report_generator.py`: xuất JSON theo `DATA_SCHEMA.md`
- [x] Xuất Excel 4 sheet, **format màu** (header, banded rows, highlight phế liệu, freeze, filter)
- [x] **Summary thêm % sử dụng** (`used_percent` = used_mm ÷ stock_mm_used)

## Phase 4 — Optimizer (đã triển khai)

- [x] `optimizer.py`: greedy ngẫu nhiên + restart, chọn join pattern tốt nhất
- [x] Giới hạn số vòng lặp (`--restarts` / `config.MAX_RESTARTS`)

## Phase 5 — CLI / main.py

- [x] `main.py`: orchestrator, argparse
- [x] Cờ `--input` (Excel, mặc định data/input.xlsx) — vẫn giữ `--stock`/`--required` (CSV)
- [x] **Tự mở file Excel** sau khi chạy (cờ `--no-open` để tắt)
- [x] `run_demo.py`: chạy nhanh với `data/input.xlsx`
- [x] In **% sử dụng** ra console

## Ghi chú cho Cline

- Mỗi phase commit riêng, không gộp nhiều phase trong 1 lần code.
- Ưu tiên đơn giản, dễ đọc hơn tối ưu tốc độ (dữ liệu bài toán này nhỏ, không
  cần lo hiệu năng).
- Nếu gặp case chưa rõ (vd nhiều loại stock length cùng lúc), dừng lại hỏi
  trước khi tự quyết định.
- Hiện chỉ hỗ trợ **1 loại stock_length**; nếu gặp nhiều loại, `run_cutting` /
  `run_cutting_optimized` báo `ValueError` và dừng lại hỏi.
- **Cấu hình rule**: mọi rule kỹ thuật (đoạn tối thiểu, bước rời rạc hóa, ngưỡng
  remnant, số lần restart) tập trung tại `config.py`. Muốn đổi 1/3 → 1/4 hay
  2000mm, chỉ sửa `config.py`, không cần đụng logic code.
- **Input chính**: `data/input.xlsx` (2 sheet). Tạo mẫu bằng `python create_input_excel.py`.
