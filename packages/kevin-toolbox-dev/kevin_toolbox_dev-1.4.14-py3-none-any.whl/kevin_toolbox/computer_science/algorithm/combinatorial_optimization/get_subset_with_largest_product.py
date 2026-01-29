import numpy as np
from kevin_toolbox.computer_science.algorithm.combinatorial_optimization import zero_one_knapsack_problem


def get_subset_with_largest_product(ls, upper_bound):
    """
        找出乘积不大于 upper_bound 的 ls 的最大乘积子集
            要求 ls 中的元素，以及 upper_bound 都为正数

        参数：
            ls:             <list>
            upper_bound:    <int/float>

        返回：
            product, subset
            最大子集的乘积 ， 最大子集
                当解不存在时候，返回 None, None
    """
    assert isinstance(ls, (list, tuple,)) and len(ls) > 0
    for i in ls + [upper_bound]:
        assert isinstance(i, (int, float, np.number,)) and i > 0

    _, idx_ls = zero_one_knapsack_problem(weights=[np.log(i) for i in ls],
                                          upper_bound=np.log(upper_bound + 1e-5))  # 为避免浮点数精度问题，需要为 upper_bound 添加冗余
    if idx_ls is not None and np.prod([ls[i] for i in idx_ls]) > upper_bound:
        # 如果前面添加的冗余影响了结果，导致乘积实际上已经超过了 upper_bound
        #   那么就尝试不添加冗余重新计算
        _, idx_ls = zero_one_knapsack_problem(weights=[np.log(i) for i in ls], upper_bound=np.log(upper_bound))

    if idx_ls is not None:
        subset = [ls[i] for i in idx_ls]
        product = np.prod(subset)
    else:
        product, subset = None, None
    return product, subset


if __name__ == '__main__':
    print(get_subset_with_largest_product(ls=[1.2, 3.4], upper_bound=12))
    print(get_subset_with_largest_product(ls=[1, 2, 2, 2, 2, 2, 2, 2, 2, 2], upper_bound=100))
    print(get_subset_with_largest_product(ls=[6, 15, 2, 2, 9], upper_bound=18))
    # (4.08, [1.2, 3.4])
    # (64, [2, 2, 2, 2, 2, 2])
