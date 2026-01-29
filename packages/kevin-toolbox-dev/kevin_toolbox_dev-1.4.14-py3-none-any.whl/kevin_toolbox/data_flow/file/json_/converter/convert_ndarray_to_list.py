import numpy as np
import torch


def convert_ndarray_to_list(x):
    """
        尝试将 numpy 或者 torch 数组转换为 list
    """

    if type(x) is np.ndarray:
        return x.tolist()
    elif torch.is_tensor(x):
        return x.detach().cpu().numpy().tolist()
    else:
        return x


if __name__ == '__main__':
    print(convert_ndarray_to_list(torch.ones(3, 4).cuda()))
