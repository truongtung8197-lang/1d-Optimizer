"""Unit test bắt buộc cho Phase 1 — Join Pattern Generator.

Các case kỳ vọng được tính theo config.py (đoạn tối thiểu có thể là ratio
hoặc fixed), để test luôn khớp với cấu hình đang dùng.
"""

import unittest

import config
from join_patterns import _min_segment_length, generate_2seg_patterns


class TestGenerate2SegPatterns(unittest.TestCase):
    def _assert_all_valid(self, L, stock_length, patterns):
        """Mọi pattern phải hợp lệ: a,b >= min_len (theo config), a<=b, a+b=L."""
        min_len = _min_segment_length(L)
        self.assertTrue(patterns)
        for a, b in patterns:
            self.assertGreaterEqual(a, min_len - 1e-9)
            self.assertGreaterEqual(b, min_len - 1e-9)
            self.assertLessEqual(a, b)
            self.assertAlmostEqual(a + b, L, places=3)

    def test_L7500_stock6000_has_valid_patterns(self):
        """(5000,2500) và (4500,3000) phải tồn tại (cả 2 đoạn đều hợp lệ)."""
        patterns = generate_2seg_patterns(7500, 6000)
        # Với ratio 1/3: min_len=2500 → (2500,5000) hợp lệ.
        # Với fixed 2000: min_len=2000 → (2500,5000) vẫn hợp lệ.
        self.assertIn((2500, 5000), patterns)
        self.assertIn((3000, 4500), patterns)

    def test_L7500_stock6000_rejects_6000_1500(self):
        """KHÔNG được có (6000,1500) vì 1500 quá ngắn (mọi config)."""
        patterns = generate_2seg_patterns(7500, 6000)
        self.assertNotIn((6000, 1500), patterns)
        self.assertNotIn((1500, 6000), patterns)

    def test_L7500_stock6000_all_valid(self):
        """Mọi pattern sinh ra phải hợp lệ theo rule config."""
        patterns = generate_2seg_patterns(7500, 6000)
        self._assert_all_valid(7500, 6000, patterns)

    def test_L8200_stock6000_bounds(self):
        """L=8200, stock=6000: mọi pattern hợp lệ theo rule config."""
        patterns = generate_2seg_patterns(8200, 6000)
        self._assert_all_valid(8200, 6000, patterns)

    def test_no_solution_returns_empty(self):
        """L quá lớn so với stock (vd 13000 vs 6000) → list rỗng."""
        patterns = generate_2seg_patterns(13000, 6000)
        self.assertEqual(patterns, [])

    def test_fixed_mode_2000(self):
        """Ở chế độ fixed 2000mm, L=2066 → vô nghiệm (2 đoạn >=2000 quá dài)."""
        if config.MIN_SEGMENT_MODE == "fixed" and config.MIN_SEGMENT_FIXED_MM >= 2000:
            patterns = generate_2seg_patterns(2066, 6000)
            self.assertEqual(patterns, [])


if __name__ == "__main__":
    unittest.main()
