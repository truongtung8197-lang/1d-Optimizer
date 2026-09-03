"""Dataclasses chính cho bài toán tối ưu cắt & nối thép.

Mỗi class chứa đúng thông tin cần thiết, không over-engineer.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Stock:
    """Loại thép nguyên liệu.

    Attributes:
        stock_type_id: Mã loại stock (vd "S6000").
        length_mm: Chiều dài mỗi cây (mm).
        quantity: Số cây sẵn có của loại này.
    """

    stock_type_id: str
    length_mm: float
    quantity: int


@dataclass
class Component:
    """Cấu kiện cần chế tạo.

    Attributes:
        component_id: Mã cấu kiện (vd "C-001").
        length_mm: Chiều dài cấu kiện (mm).
        quantity: Số lượng cần.
    """

    component_id: str
    length_mm: float
    quantity: int


@dataclass
class Segment:
    """Một đoạn thép sau khi cắt.

    Attributes:
        segment_id: Mã đoạn (vd "SEG-0001").
        length_mm: Chiều dài đoạn (mm).
        source: Nguồn gốc — "stock" (cắt từ cây mới) hoặc "remnant" (từ phần dư).
        parent_stock_id: Mã cây stock chứa đoạn này (vd "S6000-#001").
        role: Vai trò trong cấu kiện — "a" hoặc "b".
        used_by_component: Mã cấu kiện dùng đoạn này (None nếu là phế liệu).
    """

    segment_id: str
    length_mm: float
    source: str = "stock"
    parent_stock_id: str = ""
    role: str = ""
    used_by_component: str | None = None


@dataclass
class CutPlan:
    """Kế hoạch cắt của 1 cây stock.

    Attributes:
        stock_instance_id: Mã cây stock cụ thể (vd "S6000-#001").
        stock_type_id: Mã loại stock.
        stock_length_mm: Chiều dài cây.
        segments_cut: Danh sách đoạn được cắt từ cây này.
        remnant_length: Phần dư sau khi cắt (mm).
        remnant_reused_as: Mã segment được tái dùng cho cấu kiện nào (None nếu phế liệu).
    """

    stock_instance_id: str
    stock_type_id: str
    stock_length_mm: float
    segments_cut: list[Segment] = field(default_factory=list)
    remnant_length: float = 0.0
    remnant_reused_as: str | None = None


@dataclass
class ComponentAssembly:
    """Một cấu kiện được lắp từ 2 đoạn a-b nối bằng tăng đơ.

    Attributes:
        component_id: Mã cấu kiện.
        instance_no: Số thứ tự instance (1..quantity).
        target_length_mm: Chiều dài mục tiêu của cấu kiện.
        segment_a: Đoạn a.
        segment_b: Đoạn b.
        joint: Loại mối nối (luôn "tăng đơ").
    """

    component_id: str
    instance_no: int
    target_length_mm: float
    segment_a: Segment
    segment_b: Segment
    joint: str = "tăng đơ"

    @property
    def total_length(self) -> float:
        return self.segment_a.length_mm + self.segment_b.length_mm
