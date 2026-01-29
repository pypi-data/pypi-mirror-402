import copy
from kevin_toolbox.nested_dict_list import traverse
import torch


def copy_(var, b_deepcopy=False, b_keep_internal_references=True):
    """
        复制嵌套字典列表 var，并返回其副本

        参数：
            var
            b_deepcopy:                     <boolean> 是否进行深拷贝
                                                默认为 False 此时仅复制结构，但叶节点仍在 var 和其副本之间共享
                                                当设置为 True 时，进行完全的深拷贝
            b_keep_internal_references:     <boolean> 是否保留内部的引用关系。
                                                默认为 True（当b_deepcopy=True时与 copy.deepcopy 的行为一致）。
                                什么是引用关系？
                                    比如我们将某个字典 A 多次加入到某个 list 中，那么这个 list 中的这些字典实际上都指向内存上同一个字典，
                                    因此对其中某个字典的修改将影响到其他 list 中的其他元素。这种内存上指向同一个位置的关系就是引用。
                                当使用 b_keep_internal_references=True 时，将保留 ndl 中结构与结构之间或者节点与节点之间的引用关系。
                                    当 b_deepcopy=False 进行浅拷贝时，该参数仅作用于结构，
                                    反之则同时作用于结构和节点。
        例子：
            以下面的结构为例（<xx>表示该结构体/节点内存中的地址）：
                {<0>
                    "a": [<1>
                        {<2> 1, 2, 3},
                        {<3> 4, 5, 6},
                        {<2> 1, 2, 3}
                    ],
                    "b": [<1>
                        {<2> 1, 2, 3},
                        {<3> 4, 5, 6},
                        {<2> 1, 2, 3}
                    ],
                }

            对于 b_deepcopy=False，
            当 b_keep_internal_references=True 时，生成：
                {<5>
                    "a": [<6>
                        {<2> 1, 2, 3},
                        {<3> 4, 5, 6},
                        {<2> 1, 2, 3}
                    ],
                    "b": [<6>
                        {<2> 1, 2, 3},
                        {<3> 4, 5, 6},
                        {<2> 1, 2, 3}
                    ],
                }
            当 b_keep_internal_references=False 时，生成：
                {<5>
                    "a": [<6>
                        {<2> 1, 2, 3},
                        {<3> 4, 5, 6},
                        {<2> 1, 2, 3}
                    ],
                    "b": [<7>  # !!!
                        {<2> 1, 2, 3},
                        {<3> 4, 5, 6},
                        {<2> 1, 2, 3}
                    ],
                }

            对于 b_deepcopy=True，
            当 b_keep_internal_references=True 时，生成：
                {<5>
                    "a": [<6>
                        {<8> 1, 2, 3},
                        {<9> 4, 5, 6},
                        {<8> 1, 2, 3}
                    ],
                    "b": [<6>
                        {<8> 1, 2, 3},
                        {<9> 4, 5, 6},
                        {<8> 1, 2, 3}
                    ],
                }
            当 b_keep_internal_references=False 时，生成：
                {<5>
                    "a": [<6>
                        {<8> 1, 2, 3},
                        {<9> 4, 5, 6},
                        {<8> 1, 2, 3}
                    ],
                    "b": [<7>  # !!!
                        {<10> 1, 2, 3},  # !!!
                        {<11> 4, 5, 6},  # !!!
                        {<10> 1, 2, 3}  # !!!
                    ],
                }
    """
    if b_deepcopy:
        if b_keep_internal_references:
            try:
                res = copy.deepcopy(var)  # 更快
                return res
            except:
                pass
        res = _copy_structure(var=var, b_keep_internal_references=b_keep_internal_references)
        res = _copy_nodes(var=res, b_keep_internal_references=b_keep_internal_references)
    else:
        res = _copy_structure(var=var, b_keep_internal_references=b_keep_internal_references)

    return res


def _copy_structure(var, b_keep_internal_references):
    """
        复制结构
            只复制 ndl 中的 dict、list 结构，复制前后 ndl 中的叶节点（亦即dict、list中的元素仍然保持共享）
    """
    memo_s = dict()  # {<old_id>: <new_it>, ...}

    def converter(_, value):
        if b_keep_internal_references:
            if id(value) not in memo_s:
                memo_s[id(value)] = value.copy()
            return memo_s[id(value)]
        else:
            return value.copy()

    return traverse(var=[var], match_cond=lambda _, __, value: isinstance(value, (list, dict,)),
                    action_mode="replace", converter=converter,
                    traversal_mode="dfs_pre_order", b_traverse_matched_element=True,
                    b_skip_repeated_non_leaf_node=True)[0]


def _copy_nodes(var, b_keep_internal_references):
    """
        复制叶节点
            复制并替换 ndl 中的叶节点
    """
    memo_s = dict()  # {<old_id>: <new_it>, ...}

    def copy_item(value):
        if torch.is_tensor(value):
            return value.detach().clone()
        else:
            return copy.deepcopy(value)

    def converter(_, value):
        if b_keep_internal_references:
            if id(value) not in memo_s:
                memo_s[id(value)] = copy_item(value)
            return memo_s[id(value)]
        else:
            return copy_item(value)

    return traverse(var=[var], match_cond=lambda _, __, value: not isinstance(value, (list, dict,)),
                    action_mode="replace", converter=converter,
                    traversal_mode="dfs_pre_order", b_traverse_matched_element=True,
                    b_skip_repeated_non_leaf_node=True)[0]


if __name__ == '__main__':
    x = dict(acc=[0.66, 0.78, 0.99], )
    copy_(var=x, b_deepcopy=False)
