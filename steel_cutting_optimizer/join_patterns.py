"""Sinh các cặp (a, b) hợp lệ cho mỗi cấu kiện.

Mọi cấu kiện = đúng 2 đoạn a + b = L, nối bằng 1 tăng đơ giữa.
Điều kiện hợp lệ:
    a_min = max(L/3, L - stock_length)
    a_max = min(2*L/3, stock_length)
Nếu a_min > a_max → không có lời giải hợp lệ với stock_length này.
"""

from __future__ import annotations

import math

import config


def _min_segment_length(L: float) -> float:
    """Tính độ dài tối thiểu của mỗi đoạn theo config.

    - mode "ratio": đoạn ngắn nhất >= L * MIN_SEGMENT_RATIO
    - mode "fixed": đoạn ngắn nhất >= MIN_SEGMENT_FIXED_MM
    """
    if config.MIN_SEGMENT_MODE == "fixed":
        return config.MIN_SEGMENT_FIXED_MM
    # mặc định "ratio"
    return L * config.MIN_SEGMENT_RATIO


def generate_2seg_patterns(
    L: float, stock_length: float, step: float | None = None
) -> list[tuple[float, float]]:
    """Trả về danh sách (a, b) hợp lệ, a <= b, cách nhau `step` mm.

    Args:
        L: Chiều dài cấu kiện (mm).
        stock_length: Chiều dài cây thép nguyên liệu (mm).
        step: Bước rời rạc hoá (mm). Mặc định lấy từ config.STEP_MM.

    Returns:
        Danh sách các cặp (a, b) hợp lệ, đã sắp xếp tăng dần theo a.
        Trả về list rỗng nếu không có lời giải hợp lệ.
    """
    if step is None:
        step = config.STEP_MM
    if L <= 0 or stock_length <= 0 or step <= 0:
        return []

    # Độ dài tối thiểu mỗi đoạn theo rule trong config
    min_len = _min_segment_length(L)

    # Giới hạn lý thuyết: đoạn a nằm trong [min_len, L - min_len]
    a_min_theory = min_len
    a_max_theory = L - min_len

    # Ràng buộc stock: a <= stock_length và b = L - a <= stock_length
    a_min = max(a_min_theory, L - stock_length)
    a_max = min(a_max_theory, stock_length)

    if a_min > a_max:
        return []

    # Rời rạc hoá: a bắt đầu từ bội số của step >= a_min
    start = math.ceil(a_min / step) * step
    patterns: list[tuple[float, float]] = []
    a = start
    while a <= a_max + 1e-9:  # dung sai số thực
        b = L - a
        # Đảm bảo a <= b (tránh trùng lặp đối xứng)
        if a <= b + 1e-9:
            patterns.append((round(a, 6), round(b, 6)))
        a += step

    return patterns


def get_patterns_for_components(
    L: float, stock_length: float, step: float = 50.0
) -> list[tuple[float, float]]:
    """Wrapper: gọi generate_2seg_patterns, trả kết quả.

    Giữ interface rõ ràng cho cutting_engine gọi lại.
    """
    return generate_2seg_patterns(L, stock_length, step)
