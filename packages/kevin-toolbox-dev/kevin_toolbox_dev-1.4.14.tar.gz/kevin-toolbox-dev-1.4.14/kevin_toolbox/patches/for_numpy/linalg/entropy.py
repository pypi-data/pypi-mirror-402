import numpy as np


def entropy(pdf, b_need_normalize=False):
    """
        参数：
            pdf:                    <list/array> 概率分布
            b_need_normalize:       <boolean> 是否将输出的熵归一化到 0~1 区间
                                        默认为 False，此时输出的熵遵从原始定义，其大小范围与输出概率分布的维度 n 有关，为 0 ~ log_{2}(n)
                                        当设置为 True，将会除以 log_{2}(n) 以进行归一化。
    """
    pdf = np.asarray(pdf, dtype=float).reshape(-1)
    # 将概率分布数组中小于等于0的元素设为1，避免出现log(0)的情况
    pdf = np.maximum(pdf, 1e-15)
    #
    pdf /= np.sum(pdf)
    # 计算熵值
    res = -np.sum(pdf * np.log2(pdf))
    if b_need_normalize:
        res /= np.log2(len(pdf))
    return res


if __name__ == '__main__':
    print(entropy(pdf=[0.1, 0.1, 0.7, 0.1], b_need_normalize=True))  # 0.6783898247235198
    print(entropy(pdf=[0.05, 0.05, 0.05, 0.05, 0.8], b_need_normalize=True))  # 0.4831881303119284
