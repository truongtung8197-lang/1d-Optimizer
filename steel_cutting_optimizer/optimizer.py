"""Optimizer — cải thiện lời giải cắt bằng greedy ngẫu nhiên + restart.

Chiến lược (theo ALGORITHM.md mục 3):
- Mỗi instance được xử lý theo thứ tự ngẫu nhiên (shuffle) và chọn join pattern
  có "tổng phế ước lượng" nhỏ nhất theo ngay thời điểm đó.
- Chạy nhiều lần với seed khác nhau, giữ lời giải tốt nhất
  (ít cây trước, rồi ít tổng phế liệu).
- Giới hạn số vòng lặp để tránh treo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import config
from cutting_engine import MIN_USABLE_REMNANT, CuttingResult
from models import Component, ComponentAssembly, CutPlan, Segment, Stock


@dataclass
class _Remnant:
    length: float
    stock_id: str


def _greedy_single(
    stocks: list[Stock],
    components: list[Component],
    patterns_by_component: dict[str, list[tuple[float, float]]],
    min_remnant: float,
    rng: random.Random,
) -> CuttingResult:
    """Một lần chạy greedy: shuffle instance, chọn pattern best-fit waste."""
    stock = stocks[0]
    stock_length = stock.length_mm
    total_available = stock.quantity

    instances = [
        (comp, instance_no)
        for comp in components
        for instance_no in range(1, comp.quantity + 1)
    ]
    rng.shuffle(instances)

    remnant_pool: list[_Remnant] = []
    cut_plans: dict[str, CutPlan] = {}
    assemblies: list[ComponentAssembly] = []
    warnings: list[str] = []
    stock_used = 0
    stock_counter = 0
    seg_counter = 0

    def next_seg_id() -> str:
        nonlocal seg_counter
        seg_counter += 1
        return f"SEG-{seg_counter:04d}"

    def new_stock() -> str | None:
        nonlocal stock_used, stock_counter
        if stock_used >= total_available:
            return None
        stock_used += 1
        stock_counter += 1
        sid = f"{stock.stock_type_id}-#{stock_counter:03d}"
        cut_plans[sid] = CutPlan(
            stock_instance_id=sid,
            stock_type_id=stock.stock_type_id,
            stock_length_mm=stock_length,
        )
        return sid

    def eval_waste(seg_length: float) -> float:
        """Phế ước lượng nếu đặt đoạn này ngay bây giờ."""
        best_rem = min(
            (r.length for r in remnant_pool if r.length >= seg_length), default=None
        )
        if best_rem is not None:
            return best_rem - seg_length
        return stock_length - seg_length

    def place(
        seg_length: float, role: str, comp_id: str, instance_no: int
    ) -> Segment | None:
        """Đặt đoạn vào remnant best-fit hoặc cây mới. Trả Segment hoặc None."""
        best_i = None
        best_len = float("inf")
        for i, rem in enumerate(remnant_pool):
            if rem.length >= seg_length and rem.length < best_len:
                best_i = i
                best_len = rem.length

        if best_i is not None:
            rem = remnant_pool.pop(best_i)
            new_rem = rem.length - seg_length
            if new_rem >= min_remnant:
                remnant_pool.append(_Remnant(new_rem, rem.stock_id))
            plan = cut_plans[rem.stock_id]
            plan.remnant_length = new_rem if new_rem >= min_remnant else 0.0
            seg = Segment(
                segment_id=next_seg_id(),
                length_mm=seg_length,
                source="remnant",
                parent_stock_id=rem.stock_id,
                role=role,
                used_by_component=comp_id,
            )
            plan.segments_cut.append(seg)
            plan.remnant_reused_as = comp_id
            return seg
        else:
            sid = new_stock()
            if sid is None:
                warnings.append(
                    f"Không đủ stock để cắt đoạn {seg_length}mm cho {comp_id} (role={role})"
                )
                return None
            plan = cut_plans[sid]
            rem = stock_length - seg_length
            plan.remnant_length = rem if rem >= min_remnant else 0.0
            seg = Segment(
                segment_id=next_seg_id(),
                length_mm=seg_length,
                source="stock",
                parent_stock_id=sid,
                role=role,
                used_by_component=comp_id,
            )
            plan.segments_cut.append(seg)
            if rem >= min_remnant:
                remnant_pool.append(_Remnant(rem, sid))
            return seg

    for comp, instance_no in instances:
        patterns = patterns_by_component.get(comp.component_id, [])
        if not patterns:
            warnings.append(
                f"Cấu kiện {comp.component_id} ({comp.length_mm}mm) không có pattern hợp lệ."
            )
            continue

        # Chọn pattern có tổng phế ước lượng nhỏ nhất
        best_score = float("inf")
        best_ab = patterns[0]
        for a, b in patterns:
            # Mô phỏng đặt tuần tự để ước lượng chính xác hơn
            score_a = eval_waste(a)
            score_b = eval_waste(b)
            score = score_a + score_b
            if score < best_score:
                best_score = score
                best_ab = (a, b)

        a, b = best_ab
        seg_a = place(a, "a", comp.component_id, instance_no)
        seg_b = place(b, "b", comp.component_id, instance_no)
        if seg_a is not None and seg_b is not None:
            assemblies.append(
                ComponentAssembly(
                    component_id=comp.component_id,
                    instance_no=instance_no,
                    target_length_mm=comp.length_mm,
                    segment_a=seg_a,
                    segment_b=seg_b,
                )
            )

    return CuttingResult(
        cut_plans=list(cut_plans.values()),
        assemblies=assemblies,
        warnings=warnings,
        total_stock_used=stock_used,
    )


def run_cutting_optimized(
    stocks: list[Stock],
    components: list[Component],
    patterns_by_component: dict[str, list[tuple[float, float]]],
    min_remnant: float = MIN_USABLE_REMNANT,
    max_restarts: int | None = None,
) -> CuttingResult:
    """Chạy nhiều lần greedy ngẫu nhiên, giữ lời giải tốt nhất.

    Tiêu chí so sánh: (số cây dùng, tổng phế liệu) — ít hơn là tốt hơn.

    Args:
        stocks: Danh sách loại stock.
        components: Danh sách cấu kiện.
        patterns_by_component: Map component_id → list pattern (a,b).
        min_remnant: Ngưỡng phần dư tối thiểu để tái dùng.
        max_restarts: Số lần chạy lại. Mặc định lấy từ config.MAX_RESTARTS.
    """
    if max_restarts is None:
        max_restarts = config.MAX_RESTARTS
    """Chạy nhiều lần greedy ngẫu nhiên, giữ lời giải tốt nhất.

    Tiêu chí so sánh: (số cây dùng, tổng phế liệu) — ít hơn là tốt hơn.
    """
    if not stocks:
        raise ValueError("Không có stock nguyên liệu nào.")
    if len({s.length_mm for s in stocks}) > 1:
        raise ValueError(
            "Hiện chỉ hỗ trợ 1 loại stock_length. Gặp nhiều loại, dừng lại hỏi."
        )

    best: CuttingResult | None = None
    best_key: tuple[int, float] | None = None

    for seed in range(max_restarts):
        rng = random.Random(seed)
        try:
            result = _greedy_single(
                stocks, components, patterns_by_component, min_remnant, rng
            )
        except ValueError:
            raise

        key = (
            result.total_stock_used,
            sum(p.remnant_length for p in result.cut_plans),
        )
        if best_key is None or key < best_key:
            best_key = key
            best = result

    assert best is not None
    return best
