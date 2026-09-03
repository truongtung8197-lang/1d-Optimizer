"""Unit test cho Phase 2 — Cutting Engine (FFD + Remnant Pool)."""

import unittest

from cutting_engine import run_cutting
from join_patterns import _min_segment_length, generate_2seg_patterns
from models import Component, Stock

STOCK = Stock(stock_type_id="S6000", length_mm=6000.0, quantity=500)
STOCK_LENGTH = 6000.0


def make_components() -> list[Component]:
    return [
        Component(component_id="C-001", length_mm=7500.0, quantity=10),
        Component(component_id="C-002", length_mm=8200.0, quantity=5),
        Component(component_id="C-003", length_mm=9500.0, quantity=8),
        Component(component_id="C-004", length_mm=11500.0, quantity=6),
    ]


def make_patterns(components: list[Component]) -> dict[str, list[tuple[float, float]]]:
    pats = {}
    for c in components:
        pats[c.component_id] = generate_2seg_patterns(c.length_mm, STOCK_LENGTH)
    return pats


class TestCuttingEngine(unittest.TestCase):
    def setUp(self):
        self.components = make_components()
        self.patterns = make_patterns(self.components)
        self.result = run_cutting([STOCK], self.components, self.patterns)

    def test_every_component_has_assembly(self):
        """Mỗi cấu kiện phải có 2 đoạn và tổng đúng L."""
        expected_instances = sum(c.quantity for c in self.components)
        self.assertEqual(len(self.result.assemblies), expected_instances)
        for asc in self.result.assemblies:
            self.assertAlmostEqual(asc.total_length, asc.target_length_mm, places=3)

    def test_each_segment_meets_min_rule(self):
        """Mỗi đoạn a, b phải >= min_len (theo rule trong config)."""
        for asc in self.result.assemblies:
            min_len = _min_segment_length(asc.target_length_mm)
            self.assertGreaterEqual(asc.segment_a.length_mm, min_len - 1e-9)
            self.assertGreaterEqual(asc.segment_b.length_mm, min_len - 1e-9)

    def test_cut_plan_total_matches_stock(self):
        """Mỗi cây: tổng đoạn cắt + remnant = stock_length."""
        for plan in self.result.cut_plans:
            total_cut = sum(seg.length_mm for seg in plan.segments_cut)
            self.assertAlmostEqual(
                total_cut + plan.remnant_length, plan.stock_length_mm, places=3
            )

    def test_no_segment_used_twice(self):
        """Không đoạn nào được dùng cho 2 cấu kiện khác nhau."""
        seen_ids = set()
        for plan in self.result.cut_plans:
            for seg in plan.segments_cut:
                self.assertNotIn(seg.segment_id, seen_ids)
                seen_ids.add(seg.segment_id)

    def test_all_assembly_segments_appear_in_cut_plans(self):
        """Mọi đoạn trong assembly phải nằm trong danh sách cắt của 1 cây nào đó."""
        cut_seg_ids = {
            seg.segment_id
            for plan in self.result.cut_plans
            for seg in plan.segments_cut
        }
        for asc in self.result.assemblies:
            self.assertIn(asc.segment_a.segment_id, cut_seg_ids)
            self.assertIn(asc.segment_b.segment_id, cut_seg_ids)

    def test_total_stock_used_reported(self):
        """Báo cáo tổng số cây dùng."""
        self.assertGreater(self.result.total_stock_used, 0)
        self.assertEqual(len(self.result.cut_plans), self.result.total_stock_used)


if __name__ == "__main__":
    unittest.main()
