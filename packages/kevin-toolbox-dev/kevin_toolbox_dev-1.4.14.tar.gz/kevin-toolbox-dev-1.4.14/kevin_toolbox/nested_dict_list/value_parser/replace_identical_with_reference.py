from collections import defaultdict
from kevin_toolbox.nested_dict_list import get_nodes, get_value, set_value
from kevin_toolbox.nested_dict_list import value_parser


def replace_identical_with_reference(var, flag="same", match_cond=None, b_reverse=False):
    """
        将具有相同 id 的多个节点，替换为单个节点和其多个引用的形式
            一般用于去除冗余部分，压缩 ndl 的结构

        参数：
            var:
            flag:                   <str> 引用标记头，表示该节点应该替换为指定节点的内容
                                        默认为 "same"
                                        注意，在正向过程中，如果遇到本身就是以该 flag 开头的字符串，会自动在前添加多一个 flag 以示区分，
                                            然后在逆向过程中，遇到两个 flag 标记开头的字符串将删除一个，然后跳过不处理。
            match_cond:             <func> 仅对匹配上（返回True视为匹配上）的节点进行处理
                                        函数类型为 def(name, value)
                                        其中：
                                            name            该节点在结构体中的位置
                                            value           节点的值
                                        默认不对 int、float、bool、str、None 等类型进行处理
            b_reverse:              <boolean> 是否进行逆向操作
    """
    if match_cond is None:
        match_cond = lambda name, value: not isinstance(value, (int, float, bool, str, type(None)))
    assert callable(match_cond)

    if b_reverse:
        return _reverse(var, flag)
    else:
        return _forward(var, flag, match_cond)


def _forward(var, flag, match_cond):
    id_to_height_s = defaultdict(set)
    id_to_name_s = defaultdict(set)
    height = 1
    while True:
        node_ls = get_nodes(var=var, level=-height, b_strict=True)
        if not node_ls:
            break
        for name, value in node_ls:
            if not match_cond(name, value):
                continue
            id_to_name_s[id(value)].add(name)
            id_to_height_s[id(value)] = height
        height += 1

    #
    for k, v in list(id_to_height_s.items()):
        # 仅保留有多个节点对应的 id
        if len(id_to_name_s[k]) <= 1:
            id_to_height_s.pop(k)
            id_to_name_s.pop(k)
            continue
    # 按高度排序
    id_vs_height = sorted([(k, v) for k, v in id_to_height_s.items()], key=lambda x: x[1], reverse=True)

    # 从高到低，依次将具有相同 id 的节点替换为 单个节点和多个引用 的形式
    temp = []
    processed_name_set = set()
    for k, _ in id_vs_height:
        # 找出父节点仍然未被处理的节点（亦即仍然能够访问到的节点）
        unprocessed_name_set = {n for n in id_to_name_s[k] if id(get_value(var=var, name=n, default=temp)) == k}
        if len(unprocessed_name_set) <= 1:
            continue
        # 任选其一进行保留，其余改为引用
        keep_name = unprocessed_name_set.pop()
        for name in unprocessed_name_set:
            var = set_value(var=var, name=name, value=f'<{flag}>{{{keep_name}}}', b_force=False)
        processed_name_set.update(unprocessed_name_set)

    # 将叶节点中，未被处理过，且是 str，且以 flag 开头的字符串，添加多一个 flag，以示区分
    for name, value in get_nodes(var=var, level=-1, b_strict=True):
        if name not in processed_name_set and isinstance(value, str) and value.startswith(f'<{flag}>'):
            var = set_value(var=var, name=name, value=f'<{flag}>' + value, b_force=False)

    return var


class _My_Str:
    def __init__(self, s):
        self.s = s


def _reverse(var, flag):
    # 找出叶节点中，带有2个以上 flag 标记的字符串，删除其中一个标记，并使用 _My_Str 包裹，以便与普通引用节点区分
    for name, value in get_nodes(var=var, level=-1, b_strict=True):
        if isinstance(value, str) and value.startswith(f'<{flag}><{flag}>'):
            var = set_value(var=var, name=name, value=_My_Str(value[len(flag) + 2:]), b_force=False)
    # 解释引用
    var, _ = value_parser.parse_and_eval_references(var=var, flag=flag)
    # 解除 _My_Str 包裹
    for name, value in get_nodes(var=var, level=-1, b_strict=True):
        if isinstance(value, _My_Str):
            var = set_value(var=var, name=name, value=value.s, b_force=False)
    return var


if __name__ == '__main__':
    import numpy as np
    from kevin_toolbox.nested_dict_list import copy_

    a = np.array([1, 2, 3])
    b = np.ones((2, 3))
    c = [a, b]
    d = {"a": a, "b": b}
    e = {"c1": c, "c2": c}
    x = [e, a, d, c, "<same>{@1}", "<same><same>{@1}"]

    print(x)

    y = replace_identical_with_reference(var=copy_(x, b_deepcopy=True), flag="same")
    print(y)

    x1 = replace_identical_with_reference(var=y, flag="same", b_reverse=True)
    print(x1)

    from kevin_toolbox.patches.for_test import check_consistency

    check_consistency(x, x1)
