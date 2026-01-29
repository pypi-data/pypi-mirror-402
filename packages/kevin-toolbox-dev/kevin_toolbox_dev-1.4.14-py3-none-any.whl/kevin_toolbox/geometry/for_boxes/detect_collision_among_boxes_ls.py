import numpy as np
from .detect_collision_inside_boxes import detect_collision_inside_boxes


def detect_collision_among_boxes_ls(**kwargs):
    """
        将 boxes_ls 中的每个 boxes 视为一个 item，进行碰撞检测
            本函数是在 detect_collision_between_boxes() 的基础上实现的，具体工作原理请参见该函数。

        参数：
            boxes_ls:       <list of boxes/None> 需要检测的 item
                                each boxes inside the list is an np.array with shape [batch_size, 2, dimensions]
                                各个维度的意义为：
                                    batch_size： 有多少个 box
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
                                支持使用 None 作为占位符，标记为 None 的 item 将不与任一其他 item 发生碰撞
            complexity_correction_factor_for_aixes_check:   <float/integer>
                                    参见 detect_collision_between_boxes() 的介绍
            duplicate_records:  <boolean>
                                    参见 detect_collision_between_boxes() 的介绍
        输出：
            collision_groups:   <dict of integers set> 检出的碰撞对。
                                其中的第 i 个 set 记录了 id==i 的 boxes 表示的 item 与其他哪些 items 存在碰撞
                                    比如：  collision_groups[0] = {1, 2} 表示0号 item 与1、2号 items 发生了碰撞
    """
    # 默认参数
    paras = {
        # 必要参数
        "boxes_ls": None,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert isinstance(paras["boxes_ls"], (list,))
    boxes_ls = paras["boxes_ls"]
    boxes_ls_wto_none = [boxes for boxes in boxes_ls if boxes is not None]

    if len(boxes_ls_wto_none) <= 1:
        # 单个物体没有发生碰撞
        return dict()
    # 对所有的 box 进行碰撞检测，然后消除同一个 item 内部的碰撞
    item_id_ls = [np.ones(shape=boxes.shape[0], dtype=int) * i for i, boxes in enumerate(boxes_ls) if boxes is not None]
    boxes_com = np.concatenate(boxes_ls_wto_none, axis=0)
    item_id_com = np.concatenate(item_id_ls)  # 记录各个 box 所属的 item
    collision_groups_com = detect_collision_inside_boxes(boxes=boxes_com, **kwargs)
    #
    collision_groups = dict()
    for k, v_ls in collision_groups_com.items():
        g_id = item_id_com[k]
        #
        if g_id not in collision_groups:
            collision_groups[g_id] = set()
        for v in v_ls:
            collision_groups[g_id].add(item_id_com[v])

    return collision_groups
