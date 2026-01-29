import torch
import kevin_toolbox.nested_dict_list as ndl
from kevin_toolbox.computer_science.algorithm.statistician import Accumulator_Base


class Accumulator_for_Ndl:
    """
        适用于 ndl 结构的统计器
    """

    def __init__(self, accumulator_builder):
        """
            参数：
                accumulator_builder:        ndl叶节点统计器的构造函数
        """
        assert callable(accumulator_builder) or isinstance(accumulator_builder, Accumulator_Base)
        self.accumulator_builder = accumulator_builder

        self.var = None

    def add(self, var, **kwargs):
        if self.var is None and isinstance(var, (dict, list)):
            self.var = type(var)()
        for name, value in ndl.get_nodes(var=var, level=-1, b_strict=True):
            accumulator = ndl.get_value(var=self.var, name=name, default=None)
            if accumulator is None:
                accumulator = self.accumulator_builder()
                self.var = ndl.set_value(var=self.var, name=name, value=accumulator, b_force=True)
            value = value.detach().cpu().numpy() if torch.is_tensor(value) else value
            accumulator.add(value, **kwargs)

    def add_sequence(self, var_ls, **kwargs):
        for var in var_ls:
            self.add(var, **kwargs)

    def get(self, **kwargs):
        return ndl.traverse(
            var=ndl.copy_(var=self.var, b_deepcopy=False),
            match_cond=lambda _, __, v: not isinstance(v, (dict, list)) and hasattr(v, "get"), action_mode="replace",
            converter=lambda _, v: v.get(**kwargs)
        )


if __name__ == '__main__':
    from kevin_toolbox.data_flow.file import markdown
    import numpy as np
    from kevin_toolbox.computer_science.algorithm.statistician import Average_Accumulator

    worker = Accumulator_for_Ndl(accumulator_builder=Average_Accumulator)

    worker.add({
        1: 2.1,
        "233": torch.ones(10),
        "543": [
            np.array([1, 2, 3]),
            np.array([4, 5, 6]),
        ]
    }, weight=0.8)

    worker.add({
        1: 3.1,
        "233": torch.zeros(10),
        "543": [
            np.array([0, 2, 3]),
            np.array([0, 5, 6]),
        ]
    }, weight=1.4)

    print(markdown.generate_list(var=worker.get()))
