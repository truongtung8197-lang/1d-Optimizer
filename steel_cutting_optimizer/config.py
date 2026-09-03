"""Cấu hình tập trung — nơi duy nhất để chỉnh các rule của bài toán.

Chỉ cần sửa giá trị trong file này, không cần đụng vào logic code.
"""

from __future__ import annotations

# ============================================================
# RULE ĐOẠN TỐI THIỂU (ràng buộc chịu lực)
# ------------------------------------------------------------
# Mỗi cấu kiện L được cắt thành 2 đoạn a + b = L.
# Đoạn ngắn nhất phải >= ngưỡng tối thiểu, chọn 1 trong 2 chế độ:
#
#   MIN_SEGMENT_MODE = "ratio"  → đoạn ngắn nhất >= L * MIN_SEGMENT_RATIO
#                                 (vd 1/3, 1/4, 0.3 ...)
#   MIN_SEGMENT_MODE = "fixed"  → đoạn ngắn nhất >= MIN_SEGMENT_FIXED_MM
#                                 (vd 2000, 1500 ...)
# ============================================================
MIN_SEGMENT_MODE = "ratio"  # "ratio" hoặc "fixed"
MIN_SEGMENT_RATIO = 3 / 10  # dùng khi mode = "ratio" (mặc định 1/3)
MIN_SEGMENT_FIXED_MM = 2000.0  # dùng khi mode = "fixed"

# ============================================================
# BƯỚC RỜI RẠC HÓA (dung sai cắt thực tế)
# ------------------------------------------------------------
# Các cặp (a, b) được sinh cách nhau STEP_MM mm để giới hạn số phương án.
# ============================================================
STEP_MM = 100.0

# ============================================================
# NGƯỠNG REMNANT TÁI DÙNG
# ------------------------------------------------------------
# Phần dư sau khi cắt >= MIN_USABLE_REMNANT_MM mới được giữ lại trong pool
# để tái dùng cho đoạn khác. Dưới ngưỡng này coi là phế liệu.
# ============================================================
MIN_USABLE_REMNANT_MM = 200.0

# ============================================================
# SỐ LẦN RESTART OPTIMIZER
# ------------------------------------------------------------
# Optimizer chạy MAX_RESTARTS lần với seed khác nhau, giữ lời giải tốt nhất.
# Tăng số này → kết quả có thể tốt hơn nhưng chạy lâu hơn.
# ============================================================
MAX_RESTARTS = 500
