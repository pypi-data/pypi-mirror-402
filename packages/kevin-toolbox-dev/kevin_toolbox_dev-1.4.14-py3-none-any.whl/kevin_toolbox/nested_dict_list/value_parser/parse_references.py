import re
from kevin_toolbox.nested_dict_list import get_nodes


def parse_references(var, flag="v"):
    """
        解释 var 中包含引用的值
            什么是引用？
                对于值，若为字符串类型，且其中含有 "...<flag>{ref_name}..." 的形式，则表示解释该值时需要将 <flag>{ref_name} 这部分
                替换为 var 中 ref_name 对应的值

        参数：
            var:
            flag:               <str> 引用标记头
                                    默认为 "v"
        返回：
            {name :{"expression": <str>, "paras": <dict of paras>}, ...}

        示例：
            比如对于：
                name=":z", value="<v>{:x}+<v>{:y}"
            的节点，将会返回：
                {":z": {"expression":"p_0+p_1" , "paras": {"p_0":":x","p_1":":y"}}, ...}
            利用 "expression" 和 "paras" 中的内容，将可以很方便得使用 eval() 和 get_value() 完成对节点值的计算。
            但是由于节点之间可能存在相互引用，因此一般需要通过 cal_relation_between_references() 来确定计算顺序。
    """
    pattern = f'<{flag}>' + r"\{([^{}]+?)\}"

    node_s = dict()
    for name, value in get_nodes(var=var, level=-1, b_strict=True):
        if not isinstance(value, (str,)):
            continue
        ref_names = set(re.findall(pattern=pattern, string=value))
        if len(ref_names) == 0:
            continue
        # 尝试将表达式中的 ref_name 对应部分替换成 p_x 形式的变量，方便后面使用 eval 来解释
        #       比如对于 "<v>{cfg:x}+<v>{cfg:y}" 将会产生表达式 "p_0+p_1" , {"p_0":":x","p_1":":y"}
        prefix = "p_"
        while prefix in value:
            prefix += "_"
        paras = dict()
        expression = value
        for i, var_name in enumerate(ref_names):
            p = f'{prefix}{i}'
            expression = expression.replace(f'<{flag}>{{{var_name}}}', p)
            paras[p] = var_name
        #
        node_s[name] = dict(expression=expression, paras=paras)

    return node_s
