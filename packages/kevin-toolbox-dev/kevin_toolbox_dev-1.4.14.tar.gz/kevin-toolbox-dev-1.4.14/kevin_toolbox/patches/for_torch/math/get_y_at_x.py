import torch

# 计算设备（尽量使用gpu来加速计算）
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')


def get_y_at_x(xs, ys, x, **kwargs):
    """
        对于 xs :=> ys 定义的离散函数，获取给定 x 下 y 的取值

        参数：
            xs：                 data
            ys：                 data or list of data
            mode：               插值模式
                                目前支持的模式：
                                    "pick_similar":   选取与 x 最相似的 xs 的取值，然后返回对应的 ys 中的值
            need_to_sort_xs:    是否需要先对 xs 进行排序
                                    在某些插值模式下，需要先对 xs 进行排序，然后才能进行计算
                                    默认为 False
    """
    mode = kwargs.get("mode", "pick_similar")
    assert mode in ["pick_similar", ]

    ys_ls = ys if isinstance(ys, (list, tuple,)) else [ys]
    assert len(xs) == max(map(len, ys_ls)) == min(map(len, ys_ls)) > 0

    xs = torch.tensor(xs, device=device, dtype=torch.float32) if not isinstance(xs, torch.Tensor) else xs
    for i, ys in enumerate(ys_ls):
        ys_ls[i] = torch.tensor(ys, device=device, dtype=torch.float32) if not isinstance(ys, torch.Tensor) else ys

    if kwargs.get("need_to_sort_xs", False):
        xs, sorted_indices = torch.sort(xs, dim=0)
        for i, ys in enumerate(ys_ls):
            ys_ls[i] = ys[sorted_indices.reshape(-1)]

    y_ls = []
    if mode == "pick_similar":
        gap = torch.abs(xs - x)
        index = torch.argmin(gap)
        for ys in ys_ls:
            y_ls.append(ys[index].cpu().numpy())
    assert len(y_ls) == len(ys_ls)

    res = y_ls[0] if len(y_ls) == 1 else y_ls
    return res


if __name__ == '__main__':
    import numpy as np

    xs_ = np.asarray([0.7, 0.5, 0.6, 0.4, 0.1, 0.3])
    ys_ = xs_ ** 2
    ys_2 = xs_ ** 3
    print(get_y_at_x(xs_, ys_, x=0.56))
    print(get_y_at_x(xs_, [ys_, ys_2], x=0.56))
