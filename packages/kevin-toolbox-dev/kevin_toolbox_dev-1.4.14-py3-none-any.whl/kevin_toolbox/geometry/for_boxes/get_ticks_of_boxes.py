import numpy as np


def get_ticks_of_boxes(boxes):
    """
        获取 boxes 中涉及到的坐标刻度 ticks
    """
    ticks = []
    for i in range(boxes.shape[-1]):
        tk_ls = np.asarray(sorted(list(set(boxes[..., i].flatten()))))
        ticks.append(tk_ls)

    return ticks
