"""核心选择算法：带权区间调度（weighted interval scheduling）。

纯 Python 实现，无第三方依赖，便于单独测试。

选择目标（按优先级依次裁决）：
1. 最大化入选片段的权重总和；
2. 权重总和相同时，最大化遮盖字符总数（各片段长度之和）；
3. 再相同时，入选 ID 升序列表字典序更小者胜出。

片段为左闭右开区间 [start, end)，按 Unicode 码点计数；
互不重叠允许端点相接（前一片段的 end 等于后一片段的 start 可同时入选）。
"""

from bisect import bisect_right
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

MASK_CHAR = "█"  # FULL BLOCK，单码点


@dataclass(frozen=True)
class Interval:
    """候选片段。假定已经过校验：weight 为正整数，0 <= start < end。"""

    id: str
    weight: int
    start: int
    end: int


def _better(a: Tuple[int, int, Tuple[str, ...]],
            b: Tuple[int, int, Tuple[str, ...]]) -> Tuple[int, int, Tuple[str, ...]]:
    """按 (权重总和, 遮盖字符数, 升序 ID 元组) 依次比较，返回更优解。

    权重越大越优；并列时遮盖字符数越大越优；再并列时升序 ID 列表
    字典序更小者优（Python 元组比较即字典序，公共前缀更短者更小）。
    """
    if a[0] != b[0]:
        return a if a[0] > b[0] else b
    if a[1] != b[1]:
        return a if a[1] > b[1] else b
    return a if a[2] <= b[2] else b


def select_segments(segments: Sequence[Interval]) -> List[str]:
    """从可重叠的候选片段中选出互不重叠的最优组合，返回入选 ID 升序列表。

    经典带权区间调度动态规划：按右端点排序后，
    dp[i] = max(dp[i-1], dp[p(i)] + 第 i 个区间)，
    其中 p(i) 为与第 i 个区间兼容（end <= start）的区间数量。
    字典序裁决可与 DP 组合：向两个解同时加入同一元素不会改变
    其升序列表的字典序先后，故局部最优可组合为全局最优。
    """
    # 按右端点排序是标准预处理；start、id 参与排序仅为保证结果确定性。
    ivs = sorted(segments, key=lambda s: (s.end, s.start, s.id))
    n = len(ivs)
    ends = [s.end for s in ivs]

    # p[i]：排序后与第 i 个区间兼容的区间个数（即其 dp 下标）。
    # 左闭右开区间允许端点相接，故兼容条件为 end <= start。
    p = [bisect_right(ends, ivs[i].start, 0, i) for i in range(n)]

    # dp[i] = 只考虑排序后前 i 个区间时的最优解：(权重总和, 字符总数, 升序 ID 元组)
    dp: List[Tuple[int, int, Tuple[str, ...]]] = [(0, 0, ())] * (n + 1)
    for i in range(1, n + 1):
        seg = ivs[i - 1]
        excluded = dp[i - 1]
        prev_w, prev_c, prev_ids = dp[p[i - 1]]
        included = (
            prev_w + seg.weight,
            prev_c + (seg.end - seg.start),
            tuple(sorted(prev_ids + (seg.id,))),
        )
        dp[i] = _better(excluded, included)
    return sorted(dp[n][2])


def apply_mask(text: str, spans: Iterable[Tuple[int, int]],
               mask_char: str = MASK_CHAR) -> str:
    """将 text 中每个 [start, end) 区间替换为等长（按码点）的 mask_char 序列。"""
    chars = list(text)
    for start, end in spans:
        chars[start:end] = [mask_char] * (end - start)
    return "".join(chars)
