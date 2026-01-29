import numpy as np
import torch

REGISTERED_TYPES = dict(
    float32=dict(dtype=dict(
        numpy=np.float32,
        torch=torch.float32,
    )),
    int8=dict(dtype=dict(
        numpy=np.int8,
        torch=torch.int8,
    ), range=[-128, 127]),
    uint8=dict(dtype=dict(
        numpy=np.uint8,
        torch=torch.uint8,
    ), range=[0, 255]),
)


def convert_dtype(x, target_type):
    """
        转换 dtype 数据类型
            本函数相较于 numpy 或者 pytorch 内置的转换函数，添加了根据类型自动裁剪的步骤，从而能够避免潜在的溢出情况。
            建议使用本函数替代内置的转换函数。

        参数：
            x:          <np.array/torch.tensor>
            dtype:      <string> 转换的目标类型
                            已支持的类型：
                                "float32", "int8", "uint8"
    """
    assert isinstance(target_type, (str,)) and target_type in REGISTERED_TYPES, \
        f"currently supported types are: {set(REGISTERED_TYPES.keys())}, but got a {target_type}"

    temp = REGISTERED_TYPES[target_type]
    if type(x) is np.ndarray:
        # clip
        y = x
        if "range" in temp:
            y = np.clip(y, temp["range"][0], temp["range"][1])
        # convert
        y = y.astype(dtype=temp["dtype"]["numpy"])
    elif torch.is_tensor(x):
        # clip
        y = x
        if "range" in temp:
            y = torch.clamp(y, temp["range"][0], temp["range"][1])
        # convert
        y = y.to(dtype=temp["dtype"]["torch"])
    else:
        raise TypeError(f"type of x should be np.ndarray or torch.tensor, but get a {type(x)}")

    return y


if __name__ == '__main__':
    from line_profiler import LineProfiler

    lp = LineProfiler()
    lp_wrapper = lp(convert_dtype)
    x = torch.rand([1, 3, 928, 11200], device=torch.device("cuda"))
    lp_wrapper(x=x, target_type="uint8")
    lp.print_stats()
