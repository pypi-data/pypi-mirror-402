def escape_node(node, b_reversed=False, times=1):
    """
        对键进行转义/反转义
            转义是指在取值方式对应的几个特殊字符 :|@ 前面添加 \

        参数：
            node:               键
            b_reversed:         <boolean> 是否进行反转义
                                    默认为 False
            times:              <int> 转义的次数
                                    默认为 1
                                    当 b_reversed=True 时，times 设置为 -1 时候表示进行多次反转义，直至无法进行
    """
    if not isinstance(node, (str,)):
        node = f'{node}'
    assert isinstance(times, (int,))
    if times < 0:
        assert b_reversed, f'times can be set to -1 only when de-escaping'
        times = len(node)

    len_old = len(node)
    for _ in range(times):
        if b_reversed:
            node = node.replace("\:", ":").replace("\|", "|").replace("\@", "@")
        else:
            node = node.replace(":", "\:").replace("|", "\|").replace("@", "\@")
        if len(node) == len_old:
            break
        len_old = len(node)

    return node
