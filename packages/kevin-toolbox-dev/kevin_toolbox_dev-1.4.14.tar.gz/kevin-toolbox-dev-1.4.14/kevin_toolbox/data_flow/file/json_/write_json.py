import os
import json
import copy
from kevin_toolbox.data_flow.file.json_.converter import integrate, escape_tuple_and_set, escape_non_str_dict_key
from kevin_toolbox.nested_dict_list import traverse

format_s = {
    "pretty_printed": dict(indent=4, ensure_ascii=False, sort_keys=False),
    "minified": dict(indent=None, ensure_ascii=False, sort_keys=False, separators=(',', ':'))
}


def write_json(content, file_path, converters=None, b_use_suggested_converter=False, output_format="pretty_printed"):
    """
        写入 json file

        参数：
            content:                    待写入内容
            file_path:                  <path or None> 写入路径
                                            当设置为 None 时，将直接把（经converters处理后的）待写入内容作为结果返回，而不进行实际的写入
            converters:                 <list of converters> 对写入内容中每个节点的处理方式
                                            转换器 converter 应该是一个形如 def(x): ... ; return x 的函数，具体可以参考
                                            json_.converter 中已实现的转换器
            b_use_suggested_converter:  <boolean> 是否使用建议的转换器
                                            建议使用 unescape/escape_non_str_dict_key 和 unescape/escape_tuple_and_set 这两对转换器，
                                            可以避免因 json 的读取/写入而丢失部分信息。
                                            默认为 False。
                    注意：当 converters 非 None，此参数失效，以 converters 中的具体设置为准
            output_format:              <str/dict/tuple> json的输出格式
                                            对于 str 目前支持以下取值：
                                                - "pretty_printed":     通过添加大量的空格和换行符来格式化输出，使输出更易读
                                                - "minified":           删除所有空格和换行符，使输出更紧凑
                                            默认为 pretty_printed。
                                            对于 dict，将允许使用更加细致的格式设定，比如：
                                                {"indent": 2, ensure_ascii=True}
                                            如果需要基于已有格式进行微调可以使用以下方式:
                                                ("pretty_printed", {"indent": 2, ensure_ascii=True})
    """
    global format_s
    assert isinstance(file_path, (str, type(None)))
    if isinstance(output_format, (str,)):
        output_format = format_s[output_format]
    elif isinstance(output_format, (tuple,)):
        output_format = format_s[output_format[0]]
        output_format.update(output_format[1])
    elif isinstance(output_format, (dict,)):
        pass
    else:
        raise ValueError(f'Unsupported output_format: {output_format}.')

    if converters is None and b_use_suggested_converter:
        converters = [escape_tuple_and_set, escape_non_str_dict_key]

    if converters is not None:
        converter = integrate(converters)
        content = traverse(var=[copy.deepcopy(content)],
                           match_cond=lambda _, __, ___: True, action_mode="replace",
                           converter=lambda _, x: converter(x),
                           b_traverse_matched_element=True,
                           b_skip_repeated_non_leaf_node=True)[0]

    content = json.dumps(content, **output_format)

    if file_path is not None:
        file_path = os.path.abspath(os.path.expanduser(file_path))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(content)
    else:
        return content


if __name__ == "__main__":
    a = {'rect': {'l:eft': [0, 1, 2], 'top': 67, 'right': 286, 'bottom': 332}}
    res_0 = write_json(a, file_path=None, output_format="pretty_printed")
    print(res_0)
    print(len(res_0))
    res_1 = write_json(a, file_path=None, output_format="minified")
    print(res_1)
    print(len(res_1))
