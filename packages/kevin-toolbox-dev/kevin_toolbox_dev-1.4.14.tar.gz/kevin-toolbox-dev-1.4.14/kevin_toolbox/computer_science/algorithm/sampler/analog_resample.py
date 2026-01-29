from kevin_toolbox.patches.for_numpy.random import get_rng


def analog_resample(samples, total_nums, seed=None, rng=None):
    """
        对不重复采样得到的 samples 按照整体基数 total_nums 进行模拟的重复采样
    """
    rng = get_rng(seed=seed, rng=rng)
    res = []
    if total_nums > 0:
        for i in range(len(samples)):
            idx = rng.randint(0, total_nums)
            if idx >= len(res):
                res.append(samples[i])
            else:
                res.append(res[idx])
    return res
