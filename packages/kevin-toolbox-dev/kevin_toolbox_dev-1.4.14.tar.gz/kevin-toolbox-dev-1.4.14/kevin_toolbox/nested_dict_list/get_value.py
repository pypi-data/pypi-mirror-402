from kevin_toolbox.nested_dict_list.name_handler import parse_name


def get_value(var, name, b_pop=False, **kwargs):
    """
        通过解释名字得到取值方式，然后到 var 中获取对应部分的值。

        参数：
            var:            任意支持索引取值的变量
            name:           <str/parsed_name> 名字
                                名字 name 的具体介绍参见函数 name_handler.parse_name()
                                假设 var=dict(acc=[0.66,0.78,0.99])，如果你想读取 var["acc"][1] => 0.78，那么可以将 name 写成：
                                    ":acc@1" 或者 "|acc|1" 等。
                                注意，在 name 的开头也可以添加任意非解释方式的字符，本函数将直接忽略它们，比如下面的:
                                    "var:acc@1" 和 "xxxx|acc|1" 也能正常读取。
            b_pop:          <boolean> 是否将值从 var 中移除
                                默认为 False
            default:        默认值
                                - 不设置（默认）。当取值失败时将报错。
                                - 设置为任意值。取值失败时将返回该值。
    """
    if isinstance(name, (tuple, list,)):
        assert len(name) == 3, f'invalid parsed name {name}'
        _, method_ls, node_ls = name
    else:
        _, method_ls, node_ls = parse_name(name=name, b_de_escape_node=True)

    try:
        pre, cur = None, var
        node = None
        for method, node in zip(method_ls, node_ls):
            pre, cur = cur, None
            if method == "@":
                node = eval(node)
            elif method == "|":
                try:
                    _ = pre[node]
                except:
                    node = eval(node)
            cur = pre[node]

        if b_pop and len(node_ls) > 0:
            assert isinstance(pre, (dict, list,)), \
                f'pop is only supported when the parent node type is list or dict, but got a {type(pre)}'
            pre.pop(node)
    except:
        if "default" in kwargs:
            cur = kwargs["default"]
        else:
            raise IndexError(f'invalid name {name}')

    return cur


if __name__ == "__main__":
    var_ = dict(acc=[0.66, 0.78, 0.99])
    print(get_value(var_, ''))
    print(get_value(var_, ['', [], []]))
