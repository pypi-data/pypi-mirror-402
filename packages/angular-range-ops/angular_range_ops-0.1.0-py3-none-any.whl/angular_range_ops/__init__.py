#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模块名称: ops.py
功能描述: 角度区间操作工具模块

本模块提供了高效的区间操作算法，支持多个区间的交集、并集、差集运算。
采用扫描线算法，可以一次性处理多个区间，效率高。

区间表示说明：
    区间以 [start, end] 的形式表示，其中 start 和 end 可以是任意实数（包括负数和大于360的数）。

    正常情况 (end >= start)：
        - [10, 100] 表示从10度到100度的区间，跨度为90度
        - [350, 370] 表示从350度经过0度到10度的区间（跨越周期边界），跨度为20度

    特殊情况 (end < start)：
        当 end < start 时，表示区间从 start 递增，跨越了周期终点(360度)，然后走到 end 的位置。
        - [350, 10] 表示从350度经过360/0度到10度的区间，跨度为20度
        - [10, -10] 表示从10度递增，经过360度到达-10度(即350度)，跨度为340度
        - [-350, -370] 表示从-350度(即10度)递增，经过-360/0到达-370度(即350度)，跨度为340度

        处理方式：当发现 end < start 时，直接对 end 做 end += 360 处理，然后进行标准化。

核心算法思想：
    1. 收集所有区间的起止点作为分界点
    2. 将分界点归一化到[0, 360)范围
    3. 用分界点将[0, 360)分割成多个子区间
    4. 构建映射矩阵：子区间中点 × 原始区间 → 0/1矩阵
    5. 根据矩阵模式计算交集、并集、差集

主要功能:
    1. normalize_range: 将区间归一化到[0, 360)范围，支持 end < start 的跨界表示
    2. split_range: 处理跨越0/360度边界的区间
    3. point_in_range: 判断点是否在区间内
    4. build_coverage_matrix: 构建覆盖矩阵
    5. intersection: 多区间交集运算
    6. union: 多区间并集运算
    7. difference: 区间差集运算
    8. merge_ranges: 合并相邻区间

作者: wangheng
创建日期: 2024
版本: 2.1.0
Python版本: 3.9+
"""

from typing import List, Tuple


# 浮点数比较的精度阈值
EPSILON = 1e-9


def normalize_angle(angle: float) -> float:
    """
    将角度归一化到[0, 360)范围

    Args:
        angle: 输入角度

    Returns:
        归一化后的角度，范围[0, 360)
    """
    result = angle % 360
    if result < 0:
        result += 360
    return result


def normalize_range(range_: List[float]) -> List[float]:
    """
    将区间归一化，确保起点在[0, 360)范围内，保持区间长度不变

    支持 end < start 的情况，表示跨越周期边界的区间：
    - [350, 10] 表示从350度经过0度到10度
    - [10, -10] 表示从10度经过360度到达-10度(即350度)

    处理方式：
    1. 如果 end < start，先对 end 执行 end += 360，转换为标准 end >= start 的形式
    2. 然后进行标准的归一化处理

    Args:
        range_: 区间 [start, end]，其中 start 和 end 可以是任意实数

    Returns:
        归一化后的区间，起点在[0, 360)，终点 = 起点 + 区间长度
        如果是空区间或长度 >= 360，返回相应的特殊值
    """
    if not range_ or len(range_) != 2:
        return []

    start, end = range_[0], range_[1]

    # 处理 end < start 的情况：表示跨越周期边界
    if end < start:
        end += 360

    # 空区间
    if abs(end - start) < EPSILON:
        return []

    # 归一化起点
    norm_start = normalize_angle(start)

    # 计算区间长度
    length = end - start

    # 如果长度 >= 360，表示覆盖整个圆
    if length >= 360 - EPSILON:
        return [0, 360]

    # 归一化终点
    norm_end = norm_start + length

    return [norm_start, norm_end]


def split_range(range_: List[float]) -> List[List[float]]:
    """
    将跨越360度边界的区间分割成两个区间

    Args:
        range_: 归一化后的区间 [start, end]，其中 start 在 [0, 360)，end 可能 >= 360

    Returns:
        分割后的区间列表，每个区间都在[0, 360)范围内
    """
    if not range_ or len(range_) != 2:
        return []

    start, end = range_[0], range_[1]

    # 空区间
    if abs(end - start) < EPSILON:
        return []

    # 完整覆盖
    if end - start >= 360 - EPSILON:
        return [[0, 360]]

    # 不跨界
    if end <= 360 + EPSILON:
        return [[start, min(end, 360)]]

    # 跨界：分成两个区间
    return [[start, 360], [0, end - 360]]


def point_in_range(point: float, range_: List[float]) -> bool:
    """
    判断点是否在区间内（区间在[0, 360)范围内）

    Args:
        point: 点的位置，应该在[0, 360)范围内
        range_: 区间 [start, end]，应该在[0, 360)范围内

    Returns:
        True 如果点在区间内，否则 False
    """
    if not range_ or len(range_) != 2:
        return False

    start, end = range_[0], range_[1]

    # 使用 EPSILON 处理浮点数精度问题
    return start - EPSILON <= point <= end + EPSILON


def merge_ranges(ranges: List[List[float]]) -> List[List[float]]:
    """
    合并相邻或重叠的区间

    Args:
        ranges: 区间列表，每个区间 [start, end]

    Returns:
        合并后的区间列表
    """
    if not ranges:
        return []

    # 过滤空区间
    valid_ranges = [r for r in ranges if len(r) == 2 and abs(r[1] - r[0]) > EPSILON]

    if not valid_ranges:
        return []

    # 按起点排序
    sorted_ranges = sorted(valid_ranges, key=lambda x: x[0])

    merged = [sorted_ranges[0][:]]

    for current in sorted_ranges[1:]:
        last = merged[-1]

        # 如果当前区间与上一个区间相邻或重叠
        if current[0] <= last[1] + EPSILON:
            # 合并：扩展上一个区间的终点
            last[1] = max(last[1], current[1])
        else:
            # 不相邻，添加新区间
            merged.append(current[:])

    return merged


def build_coverage_matrix(ranges: List[List[float]]) -> Tuple[List[List[float]], List[List[int]]]:
    """
    构建覆盖矩阵

    Args:
        ranges: 输入区间列表

    Returns:
        (sub_ranges, matrix)
        - sub_ranges: 分割后的子区间列表
        - matrix: 覆盖矩阵，matrix[i][j] = 1 表示子区间i的中点在原始区间j内
    """
    if not ranges:
        return [], []

    # 步骤1: 归一化所有区间并分割跨界区间
    normalized_ranges = []
    for r in ranges:
        norm_r = normalize_range(r)
        if norm_r:
            split_ranges = split_range(norm_r)
            normalized_ranges.extend(split_ranges)

    if not normalized_ranges:
        return [], []

    # 步骤2: 收集所有分界点
    boundary_points = set()
    for r in normalized_ranges:
        boundary_points.add(r[0])
        boundary_points.add(r[1])

    # 添加0和360作为边界（如果需要）
    boundary_points.add(0)
    boundary_points.add(360)

    # 排序
    sorted_points = sorted(boundary_points)

    # 步骤3: 构建子区间
    sub_ranges = []
    for i in range(len(sorted_points) - 1):
        start = sorted_points[i]
        end = sorted_points[i + 1]
        if abs(end - start) > EPSILON:  # 忽略长度为0的区间
            sub_ranges.append([start, end])

    if not sub_ranges:
        return [], []

    # 步骤4: 构建覆盖矩阵
    matrix = []
    for sub_range in sub_ranges:
        # 计算子区间的中点
        mid_point = (sub_range[0] + sub_range[1]) / 2

        # 检查这个中点在哪些原始区间内
        row = []
        for orig_range in ranges:
            # 归一化原始区间
            norm_r = normalize_range(orig_range)
            if not norm_r:
                row.append(0)
                continue

            # 分割跨界区间
            split_ranges = split_range(norm_r)

            # 检查中点是否在任一分割区间内
            in_range = any(point_in_range(mid_point, sr) for sr in split_ranges)
            row.append(1 if in_range else 0)

        matrix.append(row)

    return sub_ranges, matrix


def intersection(ranges: List[List[float]]) -> List[List[float]]:
    """
    计算多个区间的交集（模2π意义下）

    Args:
        ranges: 区间列表，每个区间 [start, end]，单位为度

    Returns:
        交集区间列表
    """
    if not ranges:
        return []

    if len(ranges) == 1:
        norm_r = normalize_range(ranges[0])
        if not norm_r:
            return []
        return split_range(norm_r)

    # 构建覆盖矩阵
    sub_ranges, matrix = build_coverage_matrix(ranges)

    if not matrix:
        return []

    # 找出所有列都是1的行（即所有原始区间都覆盖的子区间）
    num_ranges = len(ranges)
    intersection_ranges = []

    for i, row in enumerate(matrix):
        if all(val == 1 for val in row):
            intersection_ranges.append(sub_ranges[i][:])

    # 合并相邻区间
    return merge_ranges(intersection_ranges)


def union(ranges: List[List[float]]) -> List[List[float]]:
    """
    计算多个区间的并集（模2π意义下）

    Args:
        ranges: 区间列表，每个区间 [start, end]，单位为度

    Returns:
        并集区间列表
    """
    if not ranges:
        return []

    if len(ranges) == 1:
        norm_r = normalize_range(ranges[0])
        if not norm_r:
            return []
        return split_range(norm_r)

    # 构建覆盖矩阵
    sub_ranges, matrix = build_coverage_matrix(ranges)

    if not matrix:
        return []

    # 找出至少有一列是1的行（即至少被一个原始区间覆盖的子区间）
    union_ranges = []

    for i, row in enumerate(matrix):
        if any(val == 1 for val in row):
            union_ranges.append(sub_ranges[i][:])

    # 合并相邻区间
    return merge_ranges(union_ranges)


def difference(base_range: List[float],
                                       subtract_ranges: List[List[float]]) -> List[List[float]]:
    """
    计算区间差集：base_range - union(subtract_ranges)（模2π意义下）

    Args:
        base_range: 基础区间 [start, end]
        subtract_ranges: 要减去的区间列表

    Returns:
        差集区间列表
    """
    if not base_range or len(base_range) != 2:
        return []

    if not subtract_ranges:
        norm_r = normalize_range(base_range)
        if not norm_r:
            return []
        return split_range(norm_r)

    # 将base_range和subtract_ranges合并，构建覆盖矩阵
    all_ranges = [base_range] + subtract_ranges
    sub_ranges, matrix = build_coverage_matrix(all_ranges)

    if not matrix:
        return []

    # 找出第一列是1（在base_range内）但其他列都是0（不在任何subtract_ranges内）的行
    difference_ranges = []

    for i, row in enumerate(matrix):
        if row[0] == 1 and all(val == 0 for val in row[1:]):
            difference_ranges.append(sub_ranges[i][:])

    # 合并相邻区间
    return merge_ranges(difference_ranges)

