import math
from kevin_toolbox.patches.for_numpy.random import get_rng


def sample_subset_most_evenly(inputs, ratio=None, nums=None, seed=None, rng=None, b_shuffle_the_tail=True):
    """
        对列表按给定比例or数量进行采样，并返回一个新的列表，并保证列表中每个元素在新列表中的占比尽量相近
            说明：
                根据 ratio/nums 的值，将输入列表重复复制并可能随机打乱尾部元素以保证每个元素都有等概率被选取，
                生成一个新列表，其长度约为 len(inputs) * ratio  nums。
                以 ratio 为例：
                    - 当 ratio 为整数时，返回原列表重复多次的结果；
                    - 当 ratio 为非整数时，除了重复复制整数倍部分外，
                      还会从打乱后的列表中随机选取部分元素以达到目标长度。

        参数：
            inputs:             <iterable> 输入列表或其他可迭代对象
            ratio:              <float> 采样比例，
                                    采样后新列表长度约为 len(inputs) * ratio
            nums:               <int> 采样数量。
            b_shuffle_the_tail: <boolean> 是否对尾部进行随机打乱
                                    默认为 True
            seed:               <int, optional> 随机种子，用于生成确定性随机数
                                    默认为 None
            rng:                <Random, optional> 随机数生成器实例
                        仅在b_shuffle_the_tail=True时，以上两个参数起效，且仅需指定一个即可。

    """
    if nums is None:
        assert ratio is not None
        nums = math.ceil(len(inputs) * ratio)
    assert nums >= 0
    if len(inputs) == 0 or nums == 0:
        return []

    inputs = list(inputs)
    temp = inputs.copy()
    if b_shuffle_the_tail:
        rng = get_rng(seed=seed, rng=rng)
        rng.shuffle(temp)

    outputs = [] + inputs * math.floor(nums / len(inputs)) + temp[:nums % len(inputs)]
    return outputs


if __name__ == '__main__':
    print(sample_subset_most_evenly(range(5), ratio=8 / 5, seed=114, b_shuffle_the_tail=False))
    print(sample_subset_most_evenly(range(5), ratio=8 / 5, seed=114, b_shuffle_the_tail=True))

    #
    print(sample_subset_most_evenly(range(5), nums=8, seed=114, b_shuffle_the_tail=False))
    print(sample_subset_most_evenly(range(5), nums=8, seed=114, b_shuffle_the_tail=True))
