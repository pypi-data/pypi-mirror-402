import math
import torch
import numpy as np
from kevin_toolbox.patches.for_numpy.random import get_rng
from kevin_toolbox.patches.for_numpy.random.variable import DEFAULT_SETTINGS


def cdf(x, mean=0, sigma=1):
    return (1 + math.erf((x - mean) / (sigma * 2 ** 0.5))) * 0.5


def truncated_normal(mean=0, sigma=1, low=None, high=None, size=None,
                     hit_ratio_threshold=DEFAULT_SETTINGS["truncated_normal"]["hit_ratio_threshold"],
                     expand_ratio=DEFAULT_SETTINGS["truncated_normal"]["expand_ratio"],
                     **kwargs):
    """
        从截断的高斯分布中进行随机采样

        参数：
            mean,sigma              <float> 均值、标准差
            low,high                <float> 截断边界
            size:                   <tuple/list/int/None> 输出的形状

        用于调节采样效率的超参数（与设备情况有关）：
            hit_ratio_threshold:    <float> 决定采样方式的阈值
                                        我们称 截断内的部分的概率和/1 为命中概率 hit_ratio ，亦即进行一次全区间的采样，有多大概率落在截断区间内
                                            当 hit_ratio 小于该阈值时，使用方式 2 （重要性采样）来生成，
                                            当大于阈值时，使用方式 1 采样 expand_ratio * size 个样本再挑选符合落在截断区间内的样本
                                        该参数应该根据实际情况下方式1和2的耗时差异来进行调整。
            expand_ratio:           <float> 方式1的系数
                                        要求大于 1

        其他参数：
            seed:                   <int> 随机种子
            rng:                    <Random Generator> 给定的随机采样器
                            以上参数二选一
    """
    if high is not None and low is not None:
        assert high > low
    assert expand_ratio > 1 and 0 <= hit_ratio_threshold <= 1
    rng = get_rng(**kwargs)

    raw_size = 1 if size is None else np.prod([size])
    # 计算命中概率
    cdf_high = cdf(x=high, mean=mean, sigma=sigma) if high is not None else 1
    cdf_low = cdf(x=low, mean=mean, sigma=sigma) if low is not None else 0
    hit_prob = cdf_high - cdf_low

    if hit_prob >= hit_ratio_threshold:
        # 采样方式1
        res = np.empty(raw_size)
        count = 0
        while count < raw_size:
            temp = rng.normal(mean, sigma, int((raw_size - count) / hit_prob * expand_ratio) + 1)
            if low is not None:
                temp = temp[temp >= low]
            if high is not None:
                temp = temp[temp < high]
            res[count:count + len(temp)] = temp[:raw_size - count]
            count += len(temp)
    else:
        # 采样方式2（重要性采样）
        # 从均匀分布中采样
        res = rng.uniform(cdf_low, cdf_high, raw_size)
        # 对均匀分布的样本进行逆变换得到截断正态分布的样本
        res = mean + sigma * (2 ** 0.5) * torch.erfinv(torch.from_numpy(2 * res - 1))
        res = res.numpy()

    if size is None:
        res = res[0]
    else:
        res = res.reshape(size)

    return res


if __name__ == '__main__':
    points = truncated_normal(mean=0, sigma=2, low=-3, high=None, size=10000, hit_ratio_threshold=0.01,
                              expand_ratio=1.5)

    import numpy as np
    import matplotlib.pyplot as plt

    # 绘制概率分布图
    plt.hist(points, bins=20, density=True, alpha=0.7)
    plt.xlabel('Value')
    plt.ylabel('Probability Density')
    plt.title('Uniform Distribution')
    plt.show()
