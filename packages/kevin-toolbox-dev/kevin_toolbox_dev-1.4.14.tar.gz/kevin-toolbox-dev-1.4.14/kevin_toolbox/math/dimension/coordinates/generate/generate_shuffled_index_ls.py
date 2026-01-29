import math
import numpy as np
from kevin_toolbox.math.dimension import coordinates

DEFAULT_RD = np.random.RandomState()


def generate_shuffled_index_ls(**kwargs):
    """
        对 shape 内的各个 block 中的坐标进行打乱，生成随机打乱的 index_ls
            index_ls 的具体定义参见 coordinates.convert()
            参照卷积的形式，按照 kernel_size 和 stride 对 shape 的最后几个维度进行遍历，依次对遍历经过的 block 进行内部随机打乱。
            支持通过指定 generate_indices_ls_func 来设置对 block 的遍历顺序/模式。

        参数：
            shape:                      形状
            kernel_size：                卷积核的大小
                                            默认为 None 表示使用整个 shape 作为 kernel_size
            stride：                     卷积的步长
                                            默认为 None 表示与 kernel_size 相等
            allow_duplicates:           允许出现重复值。
                                            默认为 False
            generate_func_of_traversal_order_for_blocks：  用于指定对 block 的遍历顺序
                                            默认使用 coordinates.generate(pattern="z_pattern", output_format="indices_ls") 进行遍历
                                            你也可以自定义一个根据参数 shape 生成 zip_indices 格式的坐标列表的函数，来指定遍历顺序
            seed:                       随机种子
            rd:                         随机生成器
                                            （默认不需要设置）

        blocks 相关变量的计算公式：
            第i个维度上 block 的数量 n_i = argmin_{n_i} stride[i] * n_i + kernel[i] >= shape[i]  s.t. n_i>=0
                            等效于： n_i = math.ceil( max( shape[i]-kernel[i], 0 ) / stride[i] )
            对于由 (n_i,n_j,n_k) 指定的 crop，它在原始feather map上的坐标为：
                                crop = x[ stride[i] * n_i: stride[i] * n_i + kernel[i], ... ]
    """
    # 默认参数
    paras = {
        # 必要参数
        "shape": None,
        #
        "kernel_size": None,
        "stride": None,
        "allow_duplicates": False,
        #
        "generate_func_of_traversal_order_for_blocks":
            lambda shape: coordinates.generate(pattern="z_pattern", output_format="indices_ls", shape=shape),
        #
        "seed": None,
        "rd": DEFAULT_RD,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    # shape
    if isinstance(paras["shape"], (int,)):
        paras["shape"] = [paras["shape"]]
    assert isinstance(paras["shape"], (tuple, list,)) and 0 < len(paras["shape"])
    shape = list(paras["shape"])
    # kernel_size
    if paras["kernel_size"] is None:
        paras["kernel_size"] = shape
    if isinstance(paras["kernel_size"], (int,)):
        paras["kernel_size"] = [paras["kernel_size"]] * len(shape)
    assert isinstance(paras["kernel_size"], (tuple, list,)) and 0 < len(paras["kernel_size"]) <= len(shape)
    kernel_size = list(paras["kernel_size"])
    # stride_ls
    if paras["stride"] is None:
        paras["stride"] = kernel_size
    if isinstance(paras["stride"], (int,)):
        paras["stride"] = [paras["stride"]] * len(kernel_size)
    assert isinstance(paras["stride"], (tuple, list,)) and len(paras["stride"]) == len(kernel_size)
    stride_ls = list(paras["stride"])
    # generate_func_of_traversal_order_for_blocks
    assert callable(paras["generate_func_of_traversal_order_for_blocks"])
    # 随机生成器
    assert paras["rd"] is not None
    rd = paras["rd"]
    rd.seed(paras["seed"])

    # 构建索引矩阵
    index_ls = np.arange(0, np.prod(shape))
    index_ls = index_ls.reshape(shape)
    if len(kernel_size) < len(shape):
        new_shape = [-1] + shape[-len(kernel_size):]
        index_ls = index_ls.reshape(new_shape)
    else:
        index_ls = index_ls[np.newaxis, :]

    # 构建遍历顺序
    shape_of_blocks = []
    for w, k, s in zip(shape[-len(kernel_size):], kernel_size, stride_ls):
        shape_of_blocks.append(math.ceil(max(w - k, 0) / s) + 1)
    indices = paras["generate_func_of_traversal_order_for_blocks"](shape=shape_of_blocks)
    beg_indices = indices * np.array([stride_ls])
    end_indices = beg_indices + np.array([kernel_size])

    #
    if paras["allow_duplicates"]:
        shuffle_func = lambda u: rd.choice(u.reshape(-1), u.size,
                                           replace=paras["allow_duplicates"]).reshape(u.shape)
    else:
        # permutation 稍微快一点
        shuffle_func = lambda u: rd.permutation(u.reshape(-1)).reshape(u.shape)

    # 随机打乱
    for i in range(index_ls.shape[0]):
        for beg, end in zip(beg_indices, end_indices):
            x = index_ls[i]
            slices = tuple([slice(int(b), int(e)) for b, e in zip(beg, end)])
            crop = x[slices]
            crop[:] = shuffle_func(crop[:])
            #
    index_ls = index_ls.reshape(-1)

    return index_ls


if __name__ == '__main__':
    shape = [6, 6]
    index_ls = generate_shuffled_index_ls(shape=shape, stride=[3, 3], kernel_size=[3, 3], seed=114)
    print(index_ls.reshape(shape))

    # from line_profiler import LineProfiler
    # import time
    #
    # lp = LineProfiler()
    #
    # lp_wrapper = lp(generate_shuffled_index_ls)
    # lp_wrapper(shape=[8181], seed=1145141919)
    # lp.print_stats()
    #
    # time_start = time.time()
    # generate_shuffled_index_ls(shape=[818100], seed=1145141919)
    # time_end = time.time()
    # print('time cost', time_end - time_start, 's')
