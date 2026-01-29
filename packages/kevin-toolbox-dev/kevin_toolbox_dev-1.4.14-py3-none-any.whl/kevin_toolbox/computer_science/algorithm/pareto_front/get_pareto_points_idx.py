import numpy as np
from enum import Enum


class Direction(Enum):
    """
        优化方向
    """
    MAXIMIZE = "maximize"  # 越大越好
    MINIMIZE = "minimize"  # 越小越好
    NOT_CARE = "not_care"  # 不考虑该维度


def get_pareto_points_idx(points, directions=None):
    """
        获取位于帕累托边缘上的点的序号
            这些边缘点具有的性质：与除它之外的任意一个点相比，其总有在某一个或者多个维度上具有“优势”

        参数：
            points:             <list/tuple/np.array> 点集
                                    shape: [nums, dims]
            directions:         <list/tuple of str/Direction> 各个维度的优化方向
                                    shape: [dims]
                                    目前支持以下三种优化方向：
                                        "maximize":     越大越好
                                        "minimize":     越小越好
                                        "not_care":     不考虑该维度
                                    默认为 None, 等效于 ["maximize"]*len(points)，亦即全部维度数值越大越好
        返回：
            idx_ls:             <list of index> 位于边缘的点的序号列表
    """
    points = np.asarray(points)
    assert points.ndim == 2 and len(points) > 0
    if directions is not None and not isinstance(directions, (list, tuple,)):
        directions = [directions] * points.shape[-1]
    assert directions is None or isinstance(directions, (list, tuple,)) and len(directions) == points.shape[-1]

    # 计算排序的权重
    if directions is not None:
        weights = []
        directions = [Direction(i) for i in directions]
        for i, direction in enumerate(directions):
            if direction is Direction.MAXIMIZE:
                weights.append(-points[:, i:i + 1])
            elif direction is Direction.MINIMIZE:
                weights.append(points[:, i:i + 1])
            else:  # Direction.NOT_CARE
                pass
        if len(weights) == 0:  # 全部都是 not_care，那就别找了
            return []
        weights = np.concatenate(weights, axis=1)
    else:
        weights = -points

    # 按权重进行排序
    order_names = tuple(f'{i}' for i in range(weights.shape[-1]))
    idx_ls = np.argsort(
        np.asarray([tuple(i) for i in weights.tolist()], dtype=[(n, weights.dtype) for n in order_names]),
        order=order_names
    )

    # 收集位于 pareto 边缘的点
    #   按上面得到的顺序从前往后过一遍 points
    #       - 累积所有维度上出现过的最大值
    #       - 若当前 point 在所有维度上比累积值要小，则抛弃该 point
    res = [idx_ls[0]]
    best = weights[idx_ls[0]][:]
    for idx in idx_ls[1:]:
        if np.any(best - weights[idx] > 0):
            best = np.min([best, weights[idx]], axis=0)
            res.append(idx)

    return res


if __name__ == '__main__':
    res = get_pareto_points_idx(points=[[1.5, 2], [2, 1], [1, 3], [3, 1]], directions=["maximize", "not_care"])
    print(res)
