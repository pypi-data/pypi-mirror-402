import numpy as np
from .computational_tree import Node


def split_whole_into_crops(**kwargs):
    """
        将变量 whole 按照 box_ls 指示的位置，以行优先的内存顺序，拆解成多个 crop
            系 concat_crops_into_whole() 的逆变换

        参数：
            whole:          <np.array/tensor>
            box_ls:         <list of np.arrays>
            beg_axis:       <integer> 要对 x 进行分割的轴
            computational_tree: <Node> 计算图
            return_details: <boolean> 是否以详细信息的形式返回结果
                                默认为 False，此时返回：
                                    crop_ls:  <list of np.array/tensor> 分割结果
                                当设置为 True，将返回一个 dict：
                                    details = dict(
                                        whole = <np.array/tensor>,  # 对 crop_ls 进行合并后的结果
                                        box_ls = <list of np.arrays>,  # 按照 内存顺序 对 box_ls 进行排序后的结果
                                        crop_ls = <list of np.array/tensor>,  # 按照 内存顺序 对 crop_ls 进行排序后的结果
                                        beg_axis = beg_axis,  # 对应与输入的 beg_axis
                                        computational_tree = <Node>,  # 计算图
                                    )
                （以上参数的详细介绍参见 concat_crops_in_memory_order()）
        返回：
            crop_ls 或者 details
    """
    # 默认参数
    paras = {
        # 必要参数
        "whole": None,
        "box_ls": None,
        #
        "beg_axis": 0,
        "computational_tree": None,
        "return_details": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert paras["whole"] is not None
    whole = paras["whole"]
    #
    assert isinstance(paras["box_ls"], (list,)) and paras["box_ls"][0].ndim == 2 and paras["box_ls"][0].shape[1] == 2
    box_ls = paras["box_ls"]
    #
    assert isinstance(paras["beg_axis"], (int,)) and 0 <= paras["beg_axis"] < whole.ndim
    beg_axis = paras["beg_axis"]
    # 构建计算图
    if paras["computational_tree"] is None:
        tree = Node(box_ls=box_ls)
        tree.build_tree()
        tree.init_tree()
    else:
        tree = paras["computational_tree"]
    assert isinstance(tree, (Node,))

    tree.var = whole
    tree.split(beg_axis=beg_axis)

    # 按行优先进行多级排序
    sorted_node_ls = sorted(tree.get_leaf_nodes(), key=lambda x: x.details["box_ls"][0][0].tolist())
    sorted_crop_ls = [node.var for node in sorted_node_ls]
    sorted_box_ls = [node.details["box_ls"][0] for node in sorted_node_ls]

    if paras["return_details"]:
        details = dict(
            whole=whole,
            crop_ls=sorted_crop_ls,
            box_ls=sorted_box_ls,
            beg_axis=beg_axis,
            computational_tree=tree,
        )
        return details
    else:
        return crop_ls
