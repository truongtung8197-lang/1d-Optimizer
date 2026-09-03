"""Cutting Engine — FFD + Remnant Pool.

Chiến lược (ALGORITHM.md mục 2):
1. Với mỗi Component × quantity, chọn 1 join pattern (a,b). Tạo "job đoạn"
   gồm tất cả a, b của mọi cấu kiện, sort giảm dần theo chiều dài.
2. Duy trì remnant_pool: các đoạn dư còn dùng được, sort giảm dần.
3. Với mỗi job đoạn (dài → ngắn):
   - Tìm remnant nhỏ nhất đủ chứa → cắt từ đó, phần dư mới quay lại pool.
   - Không có remnant phù hợp → mở cây stock mới, cắt, phần dư vào pool.
4. Ghi nhận CutPlan cho mỗi cây + ComponentAssembly cho mỗi cấu kiện.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import config
from models import Component, ComponentAssembly, CutPlan, Segment, Stock

# Ngưỡng remnant tái dùng — lấy từ config.py (mặc định 200mm)
MIN_USABLE_REMNANT = config.MIN_USABLE_REMNANT_MM


@dataclass
class Job:
    """Một đoạn cần cắt (từ pattern a-b của cấu kiện).

    Attributes:
        length: Chiều dài đoạn cần cắt.
        component_id: Mã cấu kiện chứa đoạn này.
        role: "a" hoặc "b".
        instance_no: Số instance của cấu kiện.
    """

    length: float
    component_id: str
    role: str
    instance_no: int


@dataclass
class _RemnantItem:
    """Một phần dư trong pool.

    Attributes:
        length: Chiều dài phần dư.
        parent_stock_id: Mã cây stock chứa phần dư này.
    """

    length: float
    parent_stock_id: str


@dataclass
class CuttingResult:
    """Kết quả toàn bộ quá trình cắt.

    Attributes:
        cut_plans: Danh sách CutPlan (mỗi cây stock).
        assemblies: Danh sách ComponentAssembly (mỗi cấu kiện).
        warnings: Danh sách cảnh báo (vd cấu kiện vô nghiệm, thiếu stock).
        total_stock_used: Số cây thực tế sử dụng.
    """

    cut_plans: list[CutPlan] = field(default_factory=list)
    assemblies: list[ComponentAssembly] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_stock_used: int = 0


def run_cutting(
    stocks: list[Stock],
    components: list[Component],
    patterns_by_component: dict[str, list[tuple[float, float]]],
    min_remnant: float = MIN_USABLE_REMNANT,
) -> CuttingResult:
    """Thực thi FFD + Remnant Pool trên toàn bộ cấu kiện.

    Args:
        stocks: Danh sách loại stock (hiện hỗ trợ 1 loại stock_length).
        components: Danh sách cấu kiện.
        patterns_by_component: Map component_id → list pattern (a,b) hợp lệ.
        min_remnant: Ngưỡng phần dư tối thiểu để tái dùng (mặc định 200mm).

    Returns:
        CuttingResult chứa cut_plans, assemblies, warnings, total_stock_used.

    Raises:
        ValueError: nếu không có stock nào, hoặc cấu kiện không có pattern.
    """
    if not stocks:
        raise ValueError("Không có stock nguyên liệu nào.")

    # Chỉ hỗ trợ 1 loại stock_length (theo quyết định phạm vi)
    lengths = {s.length_mm for s in stocks}
    if len(lengths) > 1:
        raise ValueError(
            "Hiện chỉ hỗ trợ 1 loại stock_length. Gặp nhiều loại, dừng lại hỏi."
        )
    stock_length = lengths.pop()

    total_available = sum(s.quantity for s in stocks)

    # Cảnh báo cấu kiện vô nghiệm (không có pattern hợp lệ với stock hiện có)
    warnings: list[str] = []
    for comp in components:
        if not patterns_by_component.get(comp.component_id, []):
            warnings.append(
                f"Cấu kiện {comp.component_id} ({comp.length_mm}mm) không có pattern hợp lệ với stock hiện có."
            )

    # Bước 1: tạo job đoạn (chọn pattern đầu tiên hợp lệ cho mỗi cấu kiện)
    jobs: list[Job] = []
    for comp in components:
        pats = patterns_by_component.get(comp.component_id, [])
        for instance in range(1, comp.quantity + 1):
            if not pats:
                continue
            a, b = pats[0]
            jobs.append(
                Job(
                    length=a,
                    component_id=comp.component_id,
                    role="a",
                    instance_no=instance,
                )
            )
            jobs.append(
                Job(
                    length=b,
                    component_id=comp.component_id,
                    role="b",
                    instance_no=instance,
                )
            )

    # Sort giảm dần theo chiều dài (FFD)
    jobs.sort(key=lambda j: j.length, reverse=True)

    # Trạng thái
    remnant_pool: list[_RemnantItem] = []
    cut_plans: list[CutPlan] = []
    assemblies: list[ComponentAssembly] = []
    stock_used = 0
    stock_id_counter = 0
    segment_id_counter = 0
    # Map giữ segment theo (component_id, role, instance) để ghép assembly
    seg_map: dict[tuple[str, str, int], Segment] = {}

    def next_seg_id() -> str:
        nonlocal segment_id_counter
        segment_id_counter += 1
        return f"SEG-{segment_id_counter:04d}"

    def open_new_stock() -> CutPlan | None:
        """Mở 1 cây stock mới nếu còn hàng. Trả về CutPlan đang mở."""
        nonlocal stock_used, stock_id_counter
        if stock_used >= total_available:
            return None
        stock_used += 1
        stock_id_counter += 1
        instance_id = f"{stocks[0].stock_type_id}-#{stock_id_counter:03d}"
        plan = CutPlan(
            stock_instance_id=instance_id,
            stock_type_id=stocks[0].stock_type_id,
            stock_length_mm=stock_length,
        )
        cut_plans.append(plan)
        return plan

    # Bước 3: xử lý từng job
    for job in jobs:
        # Tìm remnant nhỏ nhất đủ chứa (best-fit)
        best_idx = None
        best_len = float("inf")
        for idx, rem in enumerate(remnant_pool):
            if rem.length >= job.length and rem.length < best_len:
                best_idx = idx
                best_len = rem.length

        if best_idx is not None:
            rem = remnant_pool[best_idx]
            # Cắt từ remnant
            seg = Segment(
                segment_id=next_seg_id(),
                length_mm=job.length,
                source="remnant",
                parent_stock_id=rem.parent_stock_id,
                role=job.role,
                used_by_component=job.component_id,
            )
            seg_map[(job.component_id, job.role, job.instance_no)] = seg
            # Cập nhật remnant: giảm bớt hoặc thay thế
            new_rem_len = rem.length - job.length
            remnant_pool.pop(best_idx)
            if new_rem_len >= min_remnant:
                remnant_pool.append(
                    _RemnantItem(
                        length=new_rem_len, parent_stock_id=rem.parent_stock_id
                    )
                )
            # Cập nhật remnant_length trên plan tương ứng
            for plan in cut_plans:
                if plan.stock_instance_id == rem.parent_stock_id:
                    plan.remnant_length = (
                        new_rem_len if new_rem_len >= min_remnant else 0.0
                    )
                    plan.segments_cut.append(seg)
                    # ghi remnant_reused_as (đoạn từ remnant này dùng cho component nào)
                    plan.remnant_reused_as = job.component_id
        else:
            # Mở cây stock mới
            plan = open_new_stock()
            if plan is None:
                warnings.append(
                    f"Không đủ stock để cắt đoạn {job.length}mm cho {job.component_id} (role={job.role})"
                )
                continue
            seg = Segment(
                segment_id=next_seg_id(),
                length_mm=job.length,
                source="stock",
                parent_stock_id=plan.stock_instance_id,
                role=job.role,
                used_by_component=job.component_id,
            )
            seg_map[(job.component_id, job.role, job.instance_no)] = seg
            plan.segments_cut.append(seg)
            rem_len = stock_length - job.length
            plan.remnant_length = rem_len if rem_len >= min_remnant else 0.0
            if rem_len >= min_remnant:
                remnant_pool.append(
                    _RemnantItem(length=rem_len, parent_stock_id=plan.stock_instance_id)
                )

    # Bước 4: ghép assembly (mỗi cấu kiện = 2 đoạn a-b)
    for comp in components:
        for instance in range(1, comp.quantity + 1):
            sa = seg_map.get((comp.component_id, "a", instance))
            sb = seg_map.get((comp.component_id, "b", instance))
            if sa is None or sb is None:
                warnings.append(
                    f"Cấu kiện {comp.component_id} #{instance}: thiếu đoạn a/b, bỏ qua."
                )
                continue
            assemblies.append(
                ComponentAssembly(
                    component_id=comp.component_id,
                    instance_no=instance,
                    target_length_mm=comp.length_mm,
                    segment_a=sa,
                    segment_b=sb,
                )
            )

    # Sắp xếp remnant_pool giảm dần để best-fit duyệt nhanh
    remnant_pool.sort(key=lambda r: r.length, reverse=True)

    # Set total_stock_used
    result = CuttingResult(
        cut_plans=cut_plans,
        assemblies=assemblies,
        warnings=warnings,
        total_stock_used=stock_used,
    )
    return result
