"""核心算法单元测试：仅依赖标准库，可用 `python3 -m unittest discover tests` 运行。"""

import unittest

from app.selector import Interval, apply_mask, select_segments


def iv(id, weight, start, end):
    return Interval(id=id, weight=weight, start=start, end=end)


class SelectSegmentsTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(select_segments([]), [])

    def test_single(self):
        self.assertEqual(select_segments([iv("a", 3, 0, 2)]), ["a"])

    def test_overlap_picks_higher_weight(self):
        segs = [iv("a", 5, 0, 2), iv("b", 4, 0, 4)]
        self.assertEqual(select_segments(segs), ["a"])  # 权重优先于遮盖长度

    def test_adjacent_both_selected(self):
        # 左闭右开：end == start 不算重叠，可同时入选
        segs = [iv("a", 1, 0, 2), iv("b", 1, 2, 4)]
        self.assertEqual(select_segments(segs), ["a", "b"])

    def test_weight_beats_char_count(self):
        # a 权重 5 盖 2 字符，b 权重 4 盖 4 字符：权重优先
        segs = [iv("a", 5, 0, 2), iv("b", 4, 0, 4)]
        self.assertEqual(select_segments(segs), ["a"])

    def test_char_count_tiebreak(self):
        # 权重相同，遮盖字符数多者胜
        segs = [iv("a", 2, 0, 3), iv("b", 2, 0, 2)]
        self.assertEqual(select_segments(segs), ["a"])

    def test_lex_tiebreak_multi_wins(self):
        # a+b 与 c 权重、字符数均相同，["a","b"] 字典序小于 ["c"]
        segs = [iv("a", 1, 0, 1), iv("b", 1, 1, 2), iv("c", 2, 0, 2)]
        self.assertEqual(select_segments(segs), ["a", "b"])

    def test_lex_tiebreak_single_wins(self):
        # ["a"] 字典序小于 ["b","c"]
        segs = [iv("a", 2, 0, 2), iv("b", 1, 0, 1), iv("c", 1, 1, 2)]
        self.assertEqual(select_segments(segs), ["a"])

    def test_chain_requires_dp(self):
        # a+b 权重 6 优于整段 c 权重 5
        segs = [iv("a", 3, 0, 2), iv("b", 3, 2, 4), iv("c", 5, 0, 4)]
        self.assertEqual(select_segments(segs), ["a", "b"])

    def test_disjoint_all_selected(self):
        segs = [iv("x", 1, 0, 1), iv("y", 1, 5, 6), iv("z", 1, 10, 11)]
        self.assertEqual(select_segments(segs), ["x", "y", "z"])

    def test_nested_intervals(self):
        segs = [iv("outer", 10, 0, 10), iv("in1", 6, 2, 4), iv("in2", 6, 6, 8)]
        self.assertEqual(select_segments(segs), ["in1", "in2"])  # 12 > 10

    def test_ids_sorted_in_result(self):
        segs = [iv("zeta", 1, 0, 1), iv("alpha", 1, 2, 3)]
        self.assertEqual(select_segments(segs), ["alpha", "zeta"])


class ApplyMaskTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(apply_mask("abcdef", [(1, 3)]), "a██def")

    def test_adjacent_spans_merge(self):
        self.assertEqual(apply_mask("abcdef", [(0, 2), (2, 4)]), "████ef")

    def test_unicode_code_points(self):
        # "👍🏽" 为两个码点；按码点计数应整体遮盖
        self.assertEqual(apply_mask("a👍🏽b", [(1, 3)]), "a██b")

    def test_no_spans(self):
        self.assertEqual(apply_mask("abc", []), "abc")


if __name__ == "__main__":
    unittest.main()
