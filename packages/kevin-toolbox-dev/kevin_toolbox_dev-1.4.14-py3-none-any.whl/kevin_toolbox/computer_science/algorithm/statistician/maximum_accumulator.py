import numpy as np
import torch
from kevin_toolbox.computer_science.algorithm.statistician import Accumulator_Base


class Maximum_Accumulator(Accumulator_Base):
    """
        用于计算最大值的累积器
    """

    def __init__(self, **kwargs):
        """
            参数：
                data_format:            指定数据格式
                like:                   指定数据格式
                    指定输入数据的格式，有三种方式：
                        1. 显式指定数据的形状和所在设备等。
                            data_format:        <dict of paras>
                                    其中需要包含以下参数：
                                        type_:              <str>
                                                                "numpy":        np.ndarray
                                                                "torch":        torch.tensor
                                        shape:              <list of integers>
                                        device:             <torch.device>
                                        dtype:              <torch.dtype>
                        2. 根据输入的数据，来推断出形状、设备等。
                            like:               <torch.tensor / np.ndarray / int / float>
                        3. 均不指定 data_format 和 like，此时将等到第一次调用 add()/add_sequence() 时再根据输入来自动推断。
                        以上三种方式，默认选用最后一种。
                        如果三种方式同时被指定，则优先级与对应方式在上面的排名相同。
        """
        super().__init__(**kwargs)

    def add_sequence(self, var_ls, **kwargs):
        for var in var_ls:
            self.add(var, **kwargs)

    def add(self, var, **kwargs):
        """
            添加单个数据

            参数:
                var:                数据
        """
        if self.var is None:
            self.var = var
        else:
            # 统计
            if torch.is_tensor(var):
                self.var = torch.maximum(self.var, var)
            else:
                self.var = np.maximum(self.var, var)
        self.state["total_nums"] += 1

    def get(self, **kwargs):
        """
            获取当前累加的平均值
                当未有累积时，返回 None
        """
        if len(self) == 0:
            return None
        return self.var

    @staticmethod
    def _init_state():
        """
            初始化状态
        """
        return dict(
            total_nums=0
        )


if __name__ == '__main__':

    seq = list(torch.tensor(range(1, 10))-5)
    avg = Maximum_Accumulator()
    for i, v in enumerate(seq):
        avg.add(var=v)
        print(i, v, avg.get())
