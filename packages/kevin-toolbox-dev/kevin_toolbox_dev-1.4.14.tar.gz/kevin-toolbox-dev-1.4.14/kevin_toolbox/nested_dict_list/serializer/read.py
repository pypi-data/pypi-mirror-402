import os
import tempfile
from kevin_toolbox.patches import for_os
from kevin_toolbox.data_flow.file import json_
import kevin_toolbox.nested_dict_list as ndl
from kevin_toolbox.env_info.variable_ import env_vars_parser


def read(input_path, **kwargs):
    """
        读取 input_path 中保存的嵌套字典列表

        参数：
            input_path:             <path> 文件夹或者 .tar 文件，具体结构参考 write()
            b_keep_identical_relations: <boolean> 覆盖 record.json 中记录的同名参数，该参数的作用详见 write() 中的介绍。
    """
    assert os.path.exists(input_path), f'input_path {input_path} does not exist'

    with tempfile.TemporaryDirectory(dir=os.path.dirname(input_path)) as temp_dir:
        if os.path.isfile(input_path) and input_path.endswith(".tar"):  # 解压
            for_os.unpack(source=input_path, target=temp_dir)
            input_path = os.path.join(temp_dir, os.listdir(temp_dir)[0])
        var = _read_unpacked_ndl(input_path, **kwargs)

    return var


def _read_unpacked_ndl(input_path, **kwargs):
    """
        读取 input_path 中保存的嵌套字典列表
    """
    from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND

    assert os.path.exists(input_path)

    # 读取 var
    var = json_.read(file_path=os.path.join(input_path, "var.json"), b_use_suggested_converter=True)

    # 读取 record
    record_s = dict()
    if os.path.isfile(os.path.join(input_path, "record.json")):
        record_s = json_.read(file_path=os.path.join(input_path, "record.json"), b_use_suggested_converter=True)

    # 读取被处理的节点
    processed_nodes = []
    if "processed" in record_s:
        for name, value in ndl.get_nodes(var=record_s["processed"], level=-1, b_strict=True):
            if value:
                processed_nodes.append(name)
    else:
        def converter(idx, value):
            processed_nodes.append(idx)
            return value

        ndl.traverse(
            var=var,
            match_cond=lambda _, __, value: isinstance(value, (dict,)) and "backend" in value and "name" in value,
            action_mode="replace", converter=converter, b_use_name_as_idx=True, traversal_mode="bfs",
            b_traverse_matched_element=False)

    # 恢复被处理的节点
    for name in processed_nodes:
        value = ndl.get_value(var=var, name=name)
        if isinstance(value, (dict,)) and "backend" in value and "name" in value:
            nodes_dir = env_vars_parser(value.pop("nodes_dir")) if "nodes_dir" in value else os.path.join(input_path,
                                                                                                          "nodes")
            assert os.path.exists(nodes_dir), f"nodes_dir {nodes_dir} does not exist"
            bk = SERIALIZER_BACKEND.get(name=value.pop("backend"))(folder=nodes_dir)
            ndl.set_value(var=var, name=name, value=bk.read(**value))

    #
    if "b_keep_identical_relations" in kwargs:
        record_s["b_keep_identical_relations"] = kwargs["b_keep_identical_relations"]
    if record_s.get("b_keep_identical_relations", False):
        from kevin_toolbox.nested_dict_list import value_parser
        var = value_parser.replace_identical_with_reference(var=var, flag="same", b_reverse=True)

    return var


if __name__ == '__main__':
    res = read(
        "/home/SENSETIME/xukaiming/Desktop/my_repos/python_projects/kevin_toolbox/kevin_toolbox/nested_dict_list/serializer/temp3.tar")
    print(res)
