import numpy as np
import torch
from kevin_toolbox.computer_science.algorithm.statistician import Maximum_Accumulator


class Minimum_Accumulator(Maximum_Accumulator):
    """
        用于计算最小值的累积器
    """

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
                self.var = torch.minimum(self.var, var)
            else:
                self.var = np.minimum(self.var, var)
        self.state["total_nums"] += 1


if __name__ == '__main__':
    seq = list(torch.tensor(range(1, 10)) + 5)
    avg = Minimum_Accumulator()
    for i, v in enumerate(seq):
        avg.add(var=v)
        print(i, v, avg.get())
