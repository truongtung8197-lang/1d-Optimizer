"""CLI orchestrator — chạy toàn bộ pipeline tối ưu cắt & nối thép.

Cách dùng:
    python main.py --input data/input.xlsx --out output/          # (khuyến nghị)
    python main.py --stock data/stock.csv --required ... --out output/  # CSV cũ

In kết quả tóm tắt, ví dụ cây cắt, ví dụ cấu kiện nối ra console để xem
trực tiếp; đồng thời xuất cutting_plan.json và cutting_plan.xlsx.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import config
from input_loader import load_from_excel, load_required, load_stock
from join_patterns import generate_2seg_patterns
from optimizer import run_cutting_optimized
from report_generator import export_excel, export_json

MAX_EXAMPLES = 8  # số dòng ví dụ in ra console


def build_patterns(components, stock_length: float) -> dict[str, list]:
    pats = {}
    for c in components:
        pats[c.component_id] = generate_2seg_patterns(
            c.length_mm, stock_length, config.STEP_MM
        )
    return pats


def print_summary(result) -> None:
    from report_generator import _build_summary

    summary = _build_summary(result)
    print("=== TÓM TẮT ===")
    print(f"Số cây thép sử dụng: {summary['total_stock_used']}")
    print(f"Tổng chiều dài stock đã dùng: {summary['stock_mm_used']:,.0f} mm")
    print(f"Tổng chiều dài sử dụng: {summary['used_mm']:,.0f} mm")
    print(f"% SỬ DỤNG: {summary['used_percent']}%")
    print(f"Tổng phế liệu: {summary['total_scrap_mm']:,.0f} mm")
    for k, v in sorted(summary["scrap_by_stock_type"].items()):
        print(f"  - {k}: {v:,.0f} mm")
    print()


def print_cuts(result, limit: int = MAX_EXAMPLES) -> None:
    print(f"=== VÍ DỤ CÂY CẮT (hiển thị tối đa {limit} cây) ===")
    shown = 0
    for plan in result.cut_plans:
        if shown >= limit:
            print(f"... và {len(result.cut_plans) - shown} cây khác")
            break
        parts = []
        for seg in plan.segments_cut:
            target = seg.used_by_component or "phế"
            parts.append(f"[{seg.length_mm:,.0f}mm→{target}]")
        remnant = f"dư {plan.remnant_length:,.0f}mm"
        print(
            f"{plan.stock_instance_id}: {' '.join(parts) if parts else '(không cắt)'} + {remnant}"
        )
        shown += 1
    print()


def print_assemblies(result, limit: int = MAX_EXAMPLES) -> None:
    print(f"=== VÍ DỤ CẤU KIỆN NỐI (hiển thị tối đa {limit} cấu kiện) ===")
    shown = 0
    for asc in result.assemblies:
        if shown >= limit:
            print(f"... và {len(result.assemblies) - shown} cấu kiện khác")
            break
        a = asc.segment_a
        b = asc.segment_b
        print(
            f"{asc.component_id} #{asc.instance_no}: "
            f"đoạn a {a.length_mm:,.0f}mm ({a.parent_stock_id}) + "
            f"đoạn b {b.length_mm:,.0f}mm ({b.parent_stock_id}) "
            f"= {asc.target_length_mm:,.0f}mm ✓"
        )
        shown += 1
    print()


def print_warnings(result) -> None:
    print("=== CẢNH BÁO ===")
    if result.warnings:
        for w in result.warnings:
            print(f"  ! {w}")
    else:
        print("  Không có cảnh báo.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Tối ưu cắt & nối thép hình/thanh")
    parser.add_argument(
        "--input",
        default="data/input.xlsx",
        help="Đường dẫn input Excel (2 sheet Stock+Required). Mặc định data/input.xlsx.",
    )
    parser.add_argument("--stock", default=None, help="Đường dẫn stock.csv (tùy chọn)")
    parser.add_argument(
        "--required", default=None, help="Đường dẫn required.csv (tùy chọn)"
    )
    parser.add_argument(
        "--out", default="output", help="Thư mục xuất kết quả (JSON + Excel)"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Không tự mở file Excel sau khi chạy xong",
    )
    parser.add_argument(
        "--restarts",
        type=int,
        default=None,
        help="Số lần chạy lại optimizer (mặc định lấy từ config.MAX_RESTARTS)",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = base / out_dir

    # 1. Load: ưu tiên Excel (--input) khi không truyền --stock/--required
    if args.stock is None and args.required is None:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = base / input_path
        stocks, components = load_from_excel(input_path)
    else:
        stock_path = Path(args.stock)
        if not stock_path.is_absolute():
            stock_path = base / stock_path
        req_path = Path(args.required)
        if not req_path.is_absolute():
            req_path = base / req_path
        stocks = load_stock(stock_path)
        components = load_required(req_path)

    if len({s.length_mm for s in stocks}) > 1:
        raise ValueError("Nhiều loại stock_length: tạm dừng — cần xác nhận chiến lược.")

    stock_length = next(iter({s.length_mm for s in stocks}))

    # 2. Join patterns
    patterns = build_patterns(components, stock_length)

    # 3. Cutting (optimizer: nhiều lần chạy, giữ lời giải tốt nhất)
    result = run_cutting_optimized(
        stocks, components, patterns, max_restarts=args.restarts
    )

    # 4. Xuất báo cáo
    json_path = export_json(result, out_dir / "cutting_plan.json")
    xlsx_path = export_excel(result, out_dir / "cutting_plan.xlsx")

    # 5. In kết quả
    print_summary(result)
    print_cuts(result)
    print_assemblies(result)
    print_warnings(result)
    print(f"Đã xuất: {json_path}")
    print(f"Đã xuất: {xlsx_path}")

    # 6. Tự mở file Excel để xem kết quả (trừ khi --no-open)
    if not args.no_open:
        try:
            if os.name == "nt":  # Windows
                os.startfile(str(xlsx_path))
            else:  # macOS / Linux
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([opener, str(xlsx_path)])
            print(f"Đã mở: {xlsx_path}")
        except Exception as e:
            print(f"Không thể tự mở file: {e}")


if __name__ == "__main__":
    main()
