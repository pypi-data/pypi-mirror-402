from kevin_toolbox.nested_dict_list import serializer
from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.computer_science.algorithm.registration import Registry


class Serializer_for_Registry_Execution:
    """
        用于对基于 Registry 中成员构建的执行过程进行序列化和反序列化操作
            比如对于一个含有callable成员的 Registry，我们可以使用该 recorder 将其执行过程序列化保存下来，并在需要时恢复并执行

        工作流程：
                                recover() ---> executor ---> run to get result
                                   ^
                                   |
            record(...) ---> self.record_s ---> save()
                                   ^              |
                                   |              v
                                load() <---  record_file
    """

    def __init__(self):
        self.record_s = None

    def record(self, _name=None, _registry=None, *args, **kwargs):
        """
            将参数保存到 record_s 中
        """
        return self.record_name(_name, _registry).record_paras(*args, **kwargs)

    def record_name(self, _name, _registry):
        assert isinstance(_registry, (Registry,))
        assert callable(_registry.get(name=_name, default=None))
        self.record_s = self.record_s or dict()
        self.record_s["name"] = _name
        self.record_s["registry_uid"] = _registry.uid
        return self

    def record_paras(self, *args, **kwargs):
        self.record_s = self.record_s or dict()
        self.record_s["args"] = args
        self.record_s["kwargs"] = kwargs
        return self

    def save(self, output_dir=None, b_pack_into_tar=False, b_allow_overwrite=False, **kwargs):
        """
            将 record_s 使用 ndl 持久化到文件中

            参数：
                output_dir:
                b_pack_into_tar:
                b_allow_overwrite:
            其余未列出参数请参考 ndl.serializer.write 中的介绍，常用的有：
                b_allow_overwrite
                settings
            等。
        """
        assert self.record_s is not None
        file_path = serializer.write(var=self.record_s, output_dir=output_dir, b_pack_into_tar=b_pack_into_tar,
                                     b_allow_overwrite=b_allow_overwrite, **kwargs)
        return file_path

    def load(self, input_path):
        """
            从文件中加载内容到 record_s
        """
        self.record_s = serializer.read(input_path=input_path)
        return self

    def recover(self, record_s=None):
        """
            根据 record_s 中的信息，结合 registry 构建一个执行器并返回
        """
        record_s = record_s or self.record_s
        assert record_s is not None

        func = Registry(uid=record_s["registry_uid"]).get(name=record_s["name"], default=None)
        assert callable(func)
        executor = Executor(func=func, args=record_s["args"], kwargs=record_s["kwargs"])
        return executor


execution_serializer = Serializer_for_Registry_Execution()
