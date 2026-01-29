import kevin_toolbox.nested_dict_list as ndl
from kevin_toolbox.nested_dict_list import value_parser as ndl_vp


def parse_and_eval_references(var, flag="v", converter_for_ref=None, converter_for_res=None):
    """
        解释并替换 var 中包含引用的值
            什么是引用？
                对于值，若为字符串类型，且其中含有 "...<flag>{ref_name}..." 的形式，则表示解释该值时需要将 <flag>{ref_name} 这部分
                替换为 var 中 ref_name 对应的值
            本函数系对 parse_references()，eval_references()以及 cal_relation_between_references.py()的集成，
                具体实现细节请参考这些函数

        参数：
            var:
            flag:                   <str> 引用标记头
                                        默认为 "v"

            在计算包含引用的节点的结果时，将对其执行以下方法：
            converter_for_ref:      <callable> 对被引用节点施加何种处理
                                        形如 def(idx, v): ... 的函数，其中 idx 是被引用节点的名字，v是其值，
                                        返回的结果将替换掉被引用节点中原来的值。
                                        注意：
                                            - 处理后得到的结果将替换掉原引用节点的值。（重要所以说两次）
                                            - 当同一节点被多次引用时，仅会被处理、替换一次。
            converter_for_res:      <callable> 对计算结果施加何种处理
                                        形如 def(idx, v): ... 的函数，其中 idx 是节点的名字，v是计算结果

        返回：
            var, name_ls
                var 是解释后的结果，
                name_ls 是被解释的节点名称，按照解释顺序排列
    """
    node_s = ndl_vp.parse_references(var=var, flag=flag)
    node_s, b_is_DAG, order = ndl_vp.cal_relation_between_references(node_s=node_s, b_verbose=True)
    assert b_is_DAG, \
        f'There is a circular <{flag}> reference in config'
    var = ndl_vp.eval_references(var=var, node_s=node_s, order=order,
                                 converter_for_ref=converter_for_ref, converter_for_res=converter_for_res)
    return var, order
