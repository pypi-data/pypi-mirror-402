import pytest
import numpy as np
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.computer_science.algorithm.combinatorial_optimization import zero_one_knapsack_problem
from kevin_toolbox.computer_science.algorithm.for_seq import get_subsets


def test_zero_one_knapsack_problem():
    print("test combinatorial_optimization.zero_one_knapsack_problem()")

    for _ in range(1000):
        # 随机构建输入的 weights、upper_bound 和 values
        beg = int(np.random.randint(-10, 10))
        end = int(np.random.randint(1, 10))
        if end < beg:
            beg, end = end, beg
        weights = np.random.random(np.random.randint(1, 10)) * (end - beg) + beg
        values = np.random.random(len(weights)) * (end - beg) + beg
        # upper_bound = np.random.random() * end * 2.3
        upper_bound = (np.random.random() * (end - beg) + beg) * 2.3
        if np.random.randint(0, 2):
            weights = weights.astype(int)
            upper_bound = int(upper_bound)
            values = values.astype(int)

        # 使用 zero_one_knapsack_problem() 求解
        best_v_0, idx_ls_0 = zero_one_knapsack_problem(
            weights=weights.tolist(), values=values.tolist(), upper_bound=upper_bound,
        )

        # 通过暴力搜索获取真实答案
        best_v_1, idx_ls_s = None, []
        for w_ls, v_ls, idx_ls in zip(get_subsets(inputs=weights),
                                      get_subsets(inputs=values),
                                      get_subsets(inputs=range(len(weights)))):

            if sum(w_ls) > upper_bound:
                continue
            if best_v_1 is None or sum(v_ls) > best_v_1:
                best_v_1 = sum(v_ls)
                idx_ls_s = [idx_ls]
            elif sum(v_ls) == best_v_1:
                idx_ls_s.append(idx_ls)
        if best_v_1 is None:
            idx_ls_s = [None]

        # 检验
        # print(weights, values, upper_bound)
        # print(best_v_1, best_v_0)
        check_consistency(best_v_1, best_v_0)
        assert idx_ls_0 in idx_ls_s
