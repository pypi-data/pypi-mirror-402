from kevin_toolbox.nested_dict_list import traverse


def count_leaf_node_nums(var):
    """
        获取嵌套字典列表 var 中所有叶节点的数量

        参数：
            var:                待处理数据
                                    当 var 不是 dict 或者 list 时，直接将 var 视为根节点，叶节点数量视为 0
    """
    nums = 0

    def count(_, __, v):
        nonlocal nums
        if not isinstance(v, (list, dict,)):
            nums += 1
        return False

    traverse(var=var, match_cond=count, action_mode="skip", b_use_name_as_idx=False)
    return nums
