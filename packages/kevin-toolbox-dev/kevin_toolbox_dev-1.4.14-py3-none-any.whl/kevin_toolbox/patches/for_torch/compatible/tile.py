import torch
from kevin_toolbox.env_info import version

"""
    tile(x, multiples)
    
    将 input 的各个维度按照 multiples 中的数速进行复制（占用内存）
        由于在1.7版本及其之前的 pytorch 没有 torch.tile，
        考虑到兼容性，本函数在pytorch版本过低时自动使用 x.repeat() 来实现 tile 函数

    参数：
        x:                  input tensor
        multiples:          要复制的维度
"""

if version.compare(torch.__version__, "<", "1.8", mode="short"):
    def tile(x, multiples):
        assert isinstance(multiples, (list, tuple,))
        multiples = list(multiples) + [1] * (x.ndim - len(multiples))
        return x.repeat(*multiples)
else:
    def tile(x, multiples):
        assert isinstance(multiples, (list, tuple,))
        return torch.tile(x, multiples)
