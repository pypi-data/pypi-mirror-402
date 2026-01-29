import numpy as np


def softmax(x, axis=-1, temperature=None, b_use_log_over_x=False):
    """
        一种将多个数值转换为概率分布的函数
            softmax(x)[k] = e^{x_k/t} / sum_{i}( e^{x_i/t} )

        参数：
            axis:               <int> 要对将哪一个轴转为概率分布（亦即沿着该轴求和将得到1）
                                    默认为最后一个轴
            temperature:        <float> 温度系数，起到对输入中的相对小/大值的抑制/增强作用。
                                    它是一个非负数。
                                    它越大，输出的概率分布越平缓。当趋于无穷时，输出退化为均匀分布。
                                    它越小，输出的概率分布越尖锐。当趋于0时，输出退化成狄拉克函数。
            b_use_log_over_x:   <boolean> 对输入的概率分布首先进行一次 log() 操作。
                                    默认为 False
                                    当设为 True 开启后，该函数将从 softmax 变为：
                                    softmax(log(x))[k] = x_k^{1/t} / sum_{i}( x_i^{1/t} )
    """
    x = np.asarray(x, dtype=float)

    if temperature == 0:
        # quick
        res = np.zeros_like(x)
        res = np.where(x == np.max(x, axis=axis), 1, res)
    elif b_use_log_over_x:
        # softmax(log(x))
        if temperature is not None:
            res = x ** (1 / temperature)
        else:
            res = x
    else:
        # softmax(x)
        # 为了数值稳定，减去最大值
        x = x - np.max(x, axis=axis, keepdims=True)
        #
        if temperature is not None:
            assert temperature > 0
            x /= temperature
        res = np.exp(x)
    res = res / np.sum(res, axis=axis, keepdims=True)
    return res


if __name__ == '__main__':
    print(softmax(np.asarray([0, 0.1]) * 10))
    print(softmax(np.asarray([0, 0.1]), temperature=0.1))
    print(softmax(np.asarray([[[0], [0.1]]]), temperature=0.00001, axis=1))
    print(softmax(np.asarray([[[0], [0.1]]]), temperature=0, axis=1))
    print(softmax([0, 1, 2], temperature=0.1))
    print(softmax([[5.0000e-01, 5.0000e-01],
                   [7.0000e-01, 3.0000e-01],
                   [0.0000e+00, 1.0000e+03]], axis=-1, temperature=None))
