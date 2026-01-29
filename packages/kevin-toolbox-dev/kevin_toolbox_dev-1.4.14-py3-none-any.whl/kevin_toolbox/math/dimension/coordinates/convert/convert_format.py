import numpy as np


def convert_format(**kwargs):
    """
        在各种格式的 坐标列表 之间进行转换

        参数：
            var:                输入的坐标列表。
            input_format:       <str> 描述输入的格式。
                                    要与 var 的真实格式对应。
                                    目前支持在以下三种坐标格式之间进行转换：
                                        "index_ls" , "indices_ls" , "zip_indices"
            output_format:      <str> 输出的目标格式。
            shape:              坐标所属的多维变量的形状。

        这三种坐标格式是什么？有什么区别？
            - index_ls      <np.array of integer> 坐标列表。
                                其中基本元素为 integer，每个 integer 对应着将多维变量打平 reshape(-1) 后某个元素的位置。
                                shape [n_num, ]
            - indices_ls    <np.array of np.array> 坐标列表。
                                其中每个 nparray 对应着将多维变量中某个元素的位置。
                                shape [n_num, index_num]
            - zip_indices   <tuple of np.array> 坐标列表。
                                是 indices_ls 进行维度变换后的产物。
                                shape [index_num, n_num]

            以 shape=(2,2) 的变量为例，则下面两种坐标表示方式指向的元素都是相同的：
                index_ls = [0, 1, 2, 3]
                indices_ls = [[0, 0], [0, 1], [1, 0], [1, 1]]
                zip_indices = ([0, 0, 1, 1], [0, 1, 0, 1])

        为什么要区分这三种坐标格式？
            这几种坐标有不同的使用场景，且这些场景还是比较高频出现的：
            - index_ls      在使用 np.transpose() 对 axis 进行转置，或者使用 dimension.transpose.inside_axis()
                                对 axis 内各个维度进行转置时，就需要使用 index_ls 形式的坐标来指定转置后各个 axis/维度 的位置。
            - indices_ls    遍历时有可能会用到。
            - zip_indices   适用于 numpy/torch 进行按照坐标的索引取值。
                                比如对于变量 x = [[0, 1], [2, 3]]，使用前面例子中的 zip_indices，进行下面形式的取值索引：
                                x[ zip_indices ] 就可以得到 [0, 1, 2, 3]
            如果还是看不明白，可以看一下本函数测试文件 test.py 来加深一下感受。
    """

    # 默认参数
    paras = {
        # 必要参数
        "var": None,
        "input_format": None,
        "output_format": None,
        "shape": None,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    for key in {"input_format", "output_format"}:
        assert paras[key] in {"index_ls", "indices_ls", "zip_indices"}
    #
    if paras["input_format"] == "index_ls":
        assert paras["var"].ndim == 1
    elif paras["input_format"] == "indices_ls":
        assert paras["var"].ndim == 2
    else:
        assert isinstance(paras["var"], (tuple,))

    # 转换
    if paras["input_format"] == paras["output_format"]:
        res = paras["var"]
    elif paras["input_format"] == "index_ls":
        res = _index_to_indices(index_ls=paras["var"], shape=paras["shape"])
        if paras["output_format"] == "indices_ls":
            pass
        else:
            res = _indices_to_zip_type(indices_ls=res)
    elif paras["input_format"] == "indices_ls":
        if paras["output_format"] == "index_ls":
            res = _indices_to_index(indices_ls=paras["var"], shape=paras["shape"])
        else:
            res = _indices_to_zip_type(indices_ls=paras["var"])
    else:
        res = _zip_type_to_indices(zip_indices=paras["var"])
        if paras["output_format"] == "indices_ls":
            pass
        else:
            res = _indices_to_index(indices_ls=res, shape=paras["shape"])

    return res


def _indices_to_zip_type(indices_ls):
    # res = tuple([indices_ls[:, i].astype(dtype=np.int32) for i in range(indices_ls.shape[1])])
    res = tuple(np.moveaxis(indices_ls, 1, 0).astype(dtype=np.int32))
    return res


def _zip_type_to_indices(zip_indices):
    # res = np.stack(zip_indices, axis=1)
    res = np.moveaxis(zip_indices, 1, 0)
    return res


def _indices_to_index(indices_ls, shape):
    assert indices_ls.shape[1] == len(shape)

    source = np.arange(0, np.prod(shape)).astype(dtype=np.int32).reshape(shape)
    zip_indices = _indices_to_zip_type(indices_ls)
    index_ls = source[zip_indices].reshape(-1)
    return index_ls


def _index_to_indices(index_ls, shape):
    assert index_ls.size <= np.prod(shape)

    source = np.zeros(shape=shape)
    zip_indices = np.where(source >= 0)
    indices_ls = _zip_type_to_indices(zip_indices)
    indices_ls = indices_ls[index_ls]
    return indices_ls
