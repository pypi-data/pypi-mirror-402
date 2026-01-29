from enum import Enum
from kevin_toolbox.nested_dict_list.name_handler import escape_node


class Action_Mode(Enum):
    REMOVE = "remove"
    REPLACE = "replace"
    SKIP = "skip"


class Traversal_Mode(Enum):
    DFS_PRE_ORDER = "dfs_pre_order"
    DFS_POST_ORDER = "dfs_post_order"
    BFS = "bfs"


def traverse(var, match_cond, action_mode="remove", converter=None,
             b_use_name_as_idx=False, traversal_mode="dfs_pre_order", b_traverse_matched_element=False,
             b_skip_repeated_non_leaf_node=None, cond_for_repeated_leaf_to_skip=None, **kwargs):
    """
        遍历 var 找到符合 match_cond 的元素，将其按照 action_mode 指定的操作进行处理

        参数：
            var:                待处理数据
                                    当 var 不是 dict 或者 list 时，将直接返回 var 而不做处理
            match_cond:         <func> 元素的匹配条件
                                    函数类型为 def(parent_type, idx, value): ...
                                    其中：
                                        parent_type     该元素源自哪种结构体，有两个可能传入的值： list，dict
                                        idx             该元素在结构体中的位置
                                                            当 b_use_name_as_idx=False 时，
                                                                对于列表是 index，对于字典是 key
                                                            当为 True 时，传入的是元素在整体结构中的 name 位置，name的格式和含义参考
                                                                name_handler.parse_name() 中的介绍
                                        value           元素的值
            action_mode:        <str> 如何对匹配上的元素进行处理
                                    目前支持：
                                        "remove"        将该元素移除
                                        "replace"       将该元素替换为 converter() 处理后的结果
                                        "skip":         不进行任何操作
            converter:          <func> 参见 action_mode 中的 "replace" 模式
                                    函数类型为 def(idx, value): ...
                                    其中 idx 和 value 的含义参见参数 match_cond 介绍
            traversal_mode:     <str> 遍历的模式、顺序
                                    目前支持：
                                        "dfs_pre_order"         深度优先、先序遍历
                                        "dfs_post_order"        深度优先、后序遍历
                                        "bfs"                   宽度优先
                                    默认为 "dfs_pre_order"
            b_use_name_as_idx:  <boolean> 对于 match_cond/converter 中的 idx 参数，是传入整体的 name 还是父节点的 index 或 key。
                                    默认为 False
            b_traverse_matched_element: <boolean> 对于匹配上的元素，经过处理后，是否继续遍历该元素的内容
                                    默认为 False
            b_skip_repeated_non_leaf_node:  <boolean> 是否跳过重复的非叶节点。
                                    何为重复？
                                        在内存中的id相同。
                                    默认为 None，此时将根据 action_mode 的来决定：
                                        - 对于会对节点进行修改的模式，比如 "remove" 和 "replace"，将设为 True，以避免预期外的重复转换和替换。
                                        - 对于不会修改节点内容的模式，比如 "skip"，将设为 False。
            cond_for_repeated_leaf_to_skip: <list/tuple of callable> 在叶节点位置上，遇到满足其中某个条件的重复的元素时需要跳过。
                                    要求函数接受 叶节点的值，并返回一个 boolean，表示是否匹配成功。
                                    默认为 None
    """
    assert callable(match_cond)
    action_mode = Action_Mode(action_mode)
    if action_mode is Action_Mode.REPLACE:
        assert callable(converter)
    traversal_mode = Traversal_Mode(traversal_mode)
    if b_skip_repeated_non_leaf_node is None:
        if action_mode is Action_Mode.SKIP:
            b_skip_repeated_non_leaf_node = False
        else:  # action_mode in (Action_Mode.REMOVE, Action_Mode.REPLACE)
            b_skip_repeated_non_leaf_node = True
    cond_for_repeated_leaf_to_skip = [] if cond_for_repeated_leaf_to_skip is None else cond_for_repeated_leaf_to_skip

    passed_node_ids = {"leaf": set(), "non_leaf": set()}

    if traversal_mode is Traversal_Mode.BFS:
        return _bfs(var, match_cond, action_mode, converter, b_use_name_as_idx, b_traverse_matched_element,
                    b_skip_repeated_non_leaf_node=b_skip_repeated_non_leaf_node,
                    cond_for_repeated_leaf_to_skip=cond_for_repeated_leaf_to_skip,
                    passed_node_ids=passed_node_ids)
    else:
        return _dfs(var, match_cond, action_mode, converter, b_use_name_as_idx, traversal_mode,
                    b_traverse_matched_element, pre_name="",
                    b_skip_repeated_non_leaf_node=b_skip_repeated_non_leaf_node,
                    cond_for_repeated_leaf_to_skip=cond_for_repeated_leaf_to_skip,
                    passed_node_ids=passed_node_ids)


def _bfs(var, match_cond, action_mode, converter, b_use_name_as_idx, b_traverse_matched_element,
         b_skip_repeated_non_leaf_node, cond_for_repeated_leaf_to_skip, passed_node_ids):
    temp = [("", var)]

    while len(temp):
        pre_name, it = temp.pop(0)
        if isinstance(it, (list, dict)):
            #
            if b_skip_repeated_non_leaf_node:
                if id(it) in passed_node_ids["non_leaf"]:
                    continue
                else:
                    passed_node_ids["non_leaf"].add(id(it))
            #
            keys = list(range(len(it)) if isinstance(it, list) else it.keys())
            keys.reverse()  # 反过来便于 列表 弹出元素
            idx_ls = _gen_idx(it, keys, b_use_name_as_idx, pre_name)

            # 匹配&处理
            for k, idx in zip(keys, idx_ls):
                b_matched, b_popped, b_skip = _deal(it, k, idx, match_cond, converter, action_mode,
                                                    cond_for_repeated_leaf_to_skip, passed_node_ids)
                if b_skip or b_popped or (b_matched and not b_traverse_matched_element):
                    continue
                # 添加到队尾
                temp.append((idx, it[k]))

    return var


def _dfs(var, match_cond, action_mode, converter,
         b_use_name_as_idx, traversal_mode, b_traverse_matched_element, pre_name,
         b_skip_repeated_non_leaf_node, cond_for_repeated_leaf_to_skip, passed_node_ids):
    if isinstance(var, (list, dict)):
        #
        if b_skip_repeated_non_leaf_node:
            if id(var) in passed_node_ids["non_leaf"]:
                return var
            else:
                passed_node_ids["non_leaf"].add(id(var))
        #
        keys = list(range(len(var)) if isinstance(var, list) else var.keys())
        keys.reverse()  # 反过来便于 列表 弹出元素
        idx_ls = _gen_idx(var, keys, b_use_name_as_idx, pre_name)

        #
        if traversal_mode is Traversal_Mode.DFS_PRE_ORDER:
            # 先序
            # 匹配&处理
            deal_res_ls = []
            for k, idx in zip(keys, idx_ls):
                deal_res_ls.append(_deal(var, k, idx, match_cond, converter, action_mode,
                                         cond_for_repeated_leaf_to_skip, passed_node_ids))
            # 递归遍历
            for (b_matched, b_popped, b_skip), k, idx in zip(deal_res_ls, keys, idx_ls):
                if b_skip or b_popped or (b_matched and not b_traverse_matched_element):
                    continue
                var[k] = _dfs(var[k], match_cond, action_mode, converter, b_use_name_as_idx, traversal_mode,
                              b_traverse_matched_element, idx,
                              b_skip_repeated_non_leaf_node, cond_for_repeated_leaf_to_skip, passed_node_ids)
        else:
            # 后序
            # 递归遍历
            for k, idx in zip(keys, idx_ls):
                var[k] = _dfs(var[k], match_cond, action_mode, converter, b_use_name_as_idx, traversal_mode,
                              b_traverse_matched_element, idx,
                              b_skip_repeated_non_leaf_node, cond_for_repeated_leaf_to_skip, passed_node_ids)
            # 匹配&处理
            for k, idx in zip(keys, idx_ls):
                _deal(var, k, idx, match_cond, converter, action_mode,
                      cond_for_repeated_leaf_to_skip, passed_node_ids)
    else:
        pass
    return var


def _deal(var, k, idx, match_cond, converter, action_mode,
          cond_for_repeated_leaf_to_skip, passed_node_ids):
    """处理节点"""
    b_skip = False

    if cond_for_repeated_leaf_to_skip and not isinstance(var[k], (dict, list,)) and any(
            [i(var[k]) for i in cond_for_repeated_leaf_to_skip]):
        if id(var[k]) in passed_node_ids["leaf"]:
            return None, None, True
        else:
            passed_node_ids["leaf"].add(id(var[k]))
    # 匹配
    b_matched = match_cond(type(var), idx, var[k])
    b_popped = False
    # 处理
    if b_matched:
        if action_mode is Action_Mode.REMOVE:
            var.pop(k)
            b_popped = True
        elif action_mode is Action_Mode.REPLACE:
            var[k] = converter(idx, var[k])
        else:
            pass
    return b_matched, b_popped, b_skip


def _gen_idx(var, keys, b_use_name_as_idx, pre_name):
    if b_use_name_as_idx:
        idx_ls = []
        for k in keys:
            method = "@" if isinstance(var, list) or not isinstance(k, str) else ":"
            k = escape_node(node=k, b_reversed=False, times=1)
            idx_ls.append(f'{pre_name}{method}{k}')
    else:
        idx_ls = keys
    return idx_ls
