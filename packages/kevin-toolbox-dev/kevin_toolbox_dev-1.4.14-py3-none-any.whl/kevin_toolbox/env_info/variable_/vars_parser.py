import os


class Vars_Parser:
    """
        解释以ndl命名指定位置下的变量，支持读取环境变量以及指定文件中的变量
            支持以下几种方式：
            - "SYS:<var_name>"                  系统环境变量
                                                    在 linux 系统可以通过 env 命令来打印当前的环境变量，比如家目录可以使用 SYS:HOME 来表示
            - "<path>:<ndl_name>"               读取指定路径下文件中 ndl_name 说所指定位置的变量
                                                    比如在 ~/.kvt_cfg/.path.json 中保存有 {"a": [1,2], ...}
                                                    那么可以通过 "~/.kvt_cfg/.path.json:a@1" 得到取值 2
                                                    支持 .json, .kvt, ndl 等多种文件
            什么是 ndl命名？
                具体参看 nested_dict_list 下的介绍。
    """

    def __init__(self, var_s=None, default_parse_kwargs=None):
        self.var_s = dict(
            SYS=dict(os.environ).copy(),
        )
        if "HOME" not in self.var_s["SYS"]:
            self.var_s["SYS"]["HOME"] = os.path.expanduser("~")
        from kevin_toolbox.computer_science.algorithm import for_dict
        if var_s is not None:
            self.var_s = for_dict.deep_update(stem=self.var_s, patch=var_s)
        assert default_parse_kwargs is None or isinstance(default_parse_kwargs, dict)
        self.default_parse_kwargs = default_parse_kwargs

    def __call__(self, *args, **kwargs):
        return self.parse(*args, **kwargs)

    def parse(self, name, **kwargs):
        """
            解释并替换

            参数：
                default:        默认值。
                                    当有设定时，若无法解释则返回该值。
                                    否则，若无法解释将报错。
        """
        if self.default_parse_kwargs is not None:
            kwargs.update(self.default_parse_kwargs)
        if "default" in kwargs:
            default = kwargs.pop("default")
            try:
                return self.__parse(name=name, **kwargs)
            except:
                return default
        else:
            return self.__parse(name=name, **kwargs)

    def __parse(self, name, **kwargs):
        import kevin_toolbox.nested_dict_list as ndl
        from kevin_toolbox.nested_dict_list.name_handler import parse_name
        from kevin_toolbox.data_flow.file import json_, kevin_notation

        if isinstance(name, str):
            root_node, method_ls, node_ls = parse_name(name=name, b_de_escape_node=True)
        else:
            assert isinstance(name, (tuple, list,)) and len(name) == 3, f'invalid parsed name {name}'
            root_node, method_ls, node_ls = name

        if root_node not in self.var_s:
            root_node = os.path.abspath(os.path.expanduser(root_node))
            assert os.path.exists(root_node), f'file/folder not exist: {root_node}'
            if os.path.isfile(root_node) and not root_node.endswith(".tar"):
                if root_node.endswith(".json"):  # json
                    kwargs.setdefault("b_use_suggested_converter", True)
                    var = json_.read(file_path=root_node, **kwargs)
                else:  # kevin notation
                    var = kevin_notation.read(file_path=root_node, **kwargs)
            else:
                var = ndl.serializer.read(input_path=root_node, **kwargs)
        else:
            var = self.var_s[root_node]
        res = ndl.get_value(var=var, name=(root_node, method_ls, node_ls))
        return res


if __name__ == '__main__':
    vars_parser = Vars_Parser()
    print(vars_parser.parse(
        "~/.kvt_cfg/.patches.json:for_matplotlib:common_charts:font_settings:for_non-windows-platform"))
