"""Xuất kết quả cắt ra JSON và Excel.

JSON theo DATA_SCHEMA.md:
- summary: total_stock_used, total_scrap_mm, scrap_by_stock_type, used_percent
- cuts: mỗi cây stock với segments + remnant
- assemblies: mỗi cấu kiện với đoạn a-b, joint "tăng đơ"

Excel 4 sheet: Summary, Cutting Detail, Assembly Detail, Warnings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cutting_engine import CuttingResult


def _used_mm(result: CuttingResult) -> float:
    """Tổng chiều dài đoạn đã dùng cho cấu kiện (mm)."""
    return sum(
        seg.length_mm
        for plan in result.cut_plans
        for seg in plan.segments_cut
        if seg.used_by_component is not None
    )


def _stock_mm_used(result: CuttingResult) -> float:
    """Tổng chiều dài stock đã dùng (mm) = số cây × chiều dài cây."""
    if not result.cut_plans:
        return 0.0
    stock_length = result.cut_plans[0].stock_length_mm
    return result.total_stock_used * stock_length


def _build_summary(result: CuttingResult) -> dict[str, Any]:
    total_scrap = sum(p.remnant_length for p in result.cut_plans)
    scrap_by_type: dict[str, float] = {}
    for p in result.cut_plans:
        scrap_by_type[p.stock_type_id] = (
            scrap_by_type.get(p.stock_type_id, 0.0) + p.remnant_length
        )
    used = _used_mm(result)
    stock_total = _stock_mm_used(result)
    used_percent = (used / stock_total * 100.0) if stock_total > 0 else 0.0
    return {
        "total_stock_used": result.total_stock_used,
        "total_scrap_mm": round(total_scrap, 3),
        "scrap_by_stock_type": {
            k: round(v, 3) for k, v in sorted(scrap_by_type.items())
        },
        "used_mm": round(used, 3),
        "stock_mm_used": round(stock_total, 3),
        "used_percent": round(used_percent, 2),
    }


def _build_cuts(result: CuttingResult) -> list[dict[str, Any]]:
    cuts = []
    for plan in result.cut_plans:
        segments = []
        for seg in plan.segments_cut:
            segments.append(
                {
                    "segment_id": seg.segment_id,
                    "length_mm": round(seg.length_mm, 3),
                    "source": seg.source,
                    "used_by_component": seg.used_by_component,
                }
            )
        cuts.append(
            {
                "stock_instance_id": plan.stock_instance_id,
                "stock_type_id": plan.stock_type_id,
                "segments": segments,
                "remnant_mm": round(plan.remnant_length, 3),
                "remnant_reused_as": plan.remnant_reused_as,
            }
        )
    return cuts


def _build_assemblies(result: CuttingResult) -> list[dict[str, Any]]:
    assemblies = []
    for asc in result.assemblies:
        assemblies.append(
            {
                "component_id": asc.component_id,
                "instance_no": asc.instance_no,
                "target_length_mm": round(asc.target_length_mm, 3),
                "segment_a": {
                    "segment_id": asc.segment_a.segment_id,
                    "length_mm": round(asc.segment_a.length_mm, 3),
                    "from": asc.segment_a.parent_stock_id,
                },
                "segment_b": {
                    "segment_id": asc.segment_b.segment_id,
                    "length_mm": round(asc.segment_b.length_mm, 3),
                    "from": asc.segment_b.parent_stock_id,
                },
                "joint": asc.joint,
            }
        )
    return assemblies


def build_json(result: CuttingResult) -> dict[str, Any]:
    """Xây dựng dict JSON đầy đủ theo DATA_SCHEMA.md."""
    return {
        "summary": _build_summary(result),
        "cuts": _build_cuts(result),
        "assemblies": _build_assemblies(result),
        "warnings": list(result.warnings),
    }


def export_json(result: CuttingResult, out_path: str | Path) -> Path:
    """Xuất cutting_plan.json ra file."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_json(result)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_excel(result: CuttingResult, out_path: str | Path) -> Path:
    """Xuất cutting_plan.xlsx với 4 sheet, có định dạng dễ nhìn."""
    from openpyxl import Workbook

    import excel_style as es

    wb = Workbook()

    # ---- Sheet 1: Summary ----
    ws_sum = wb.active
    ws_sum.title = "Summary"
    summary = _build_summary(result)
    ws_sum.append(["Chỉ số", "Giá trị"])
    ws_sum.append(["Tổng số cây thép sử dụng", summary["total_stock_used"]])
    ws_sum.append(["Tổng chiều dài stock đã dùng (mm)", summary["stock_mm_used"]])
    ws_sum.append(["Tổng chiều dài sử dụng (mm)", summary["used_mm"]])
    ws_sum.append(["% SỬ DỤNG", f"{summary['used_percent']}%"])
    ws_sum.append(["Tổng phế liệu (mm)", summary["total_scrap_mm"]])
    for k, v in summary["scrap_by_stock_type"].items():
        ws_sum.append([f"Phế liệu loại {k} (mm)", v])
    es.style_header(ws_sum)
    es.add_borders(ws_sum)
    es.auto_width(ws_sum)
    # In đậm dòng % sử dụng
    ws_sum["A4"].font = es.Font(bold=True, size=12)
    ws_sum["B4"].font = es.Font(bold=True, size=12, color="2F5597")

    # ---- Sheet 2: Cutting Detail ----
    ws_cut = wb.create_sheet("Cutting Detail")
    ws_cut.append(
        [
            "stock_instance_id",
            "stock_type_id",
            "segment_id",
            "length_mm",
            "used_by_component",
            "type",
            "remnant_mm",
        ]
    )
    for plan in result.cut_plans:
        if plan.segments_cut:
            for seg in plan.segments_cut:
                ws_cut.append(
                    [
                        plan.stock_instance_id,
                        plan.stock_type_id,
                        seg.segment_id,
                        seg.length_mm,
                        seg.used_by_component or "",
                        "phế" if seg.used_by_component is None else "dùng",
                        "",
                    ]
                )
            # Dòng remnant của cây này
            ws_cut.append(
                [
                    plan.stock_instance_id,
                    plan.stock_type_id,
                    "(dư)",
                    plan.remnant_length,
                    "",
                    "dư",
                    plan.remnant_length,
                ]
            )
        else:
            ws_cut.append(
                [
                    plan.stock_instance_id,
                    plan.stock_type_id,
                    "",
                    0,
                    "",
                    "dư",
                    plan.remnant_length,
                ]
            )
    es.style_header(ws_cut)
    es.add_borders(ws_cut)
    es.apply_banded_rows(ws_cut)
    es.freeze_and_filter(ws_cut, "A2")
    es.auto_width(ws_cut)
    # Tô hồng các dòng phế liệu
    for row in ws_cut.iter_rows(min_row=2, max_col=ws_cut.max_column):
        if row[5].value == "phế":
            for cell in row:
                cell.fill = es.SCRAP_FILL

    # ---- Sheet 3: Assembly Detail ----
    ws_asc = wb.create_sheet("Assembly Detail")
    ws_asc.append(
        [
            "component_id",
            "instance_no",
            "target_length_mm",
            "segment_a_id",
            "segment_a_mm",
            "segment_a_from",
            "segment_b_id",
            "segment_b_mm",
            "segment_b_from",
            "joint",
        ]
    )
    for asc in result.assemblies:
        ws_asc.append(
            [
                asc.component_id,
                asc.instance_no,
                asc.target_length_mm,
                asc.segment_a.segment_id,
                asc.segment_a.length_mm,
                asc.segment_a.parent_stock_id,
                asc.segment_b.segment_id,
                asc.segment_b.length_mm,
                asc.segment_b.parent_stock_id,
                asc.joint,
            ]
        )
    es.style_header(ws_asc)
    es.add_borders(ws_asc)
    es.apply_banded_rows(ws_asc)
    es.freeze_and_filter(ws_asc, "A2")
    es.auto_width(ws_asc)

    # ---- Sheet 4: Warnings ----
    ws_warn = wb.create_sheet("Warnings")
    ws_warn.append(["Cảnh báo"])
    es.style_header(ws_warn)
    if result.warnings:
        for w in result.warnings:
            ws_warn.append([w])
        for row in ws_warn.iter_rows(min_row=2, min_col=1, max_col=1):
            for cell in row:
                cell.font = es.WARN_FONT
    else:
        ws_warn.append(["Không có cảnh báo."])
    es.add_borders(ws_warn)
    es.auto_width(ws_warn, min_width=20, max_width=90)

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
