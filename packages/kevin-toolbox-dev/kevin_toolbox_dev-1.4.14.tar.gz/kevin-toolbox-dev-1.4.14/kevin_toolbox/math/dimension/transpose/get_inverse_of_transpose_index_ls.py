import numpy as np


def get_inverse_of_transpose_index_ls(index_ls):
    """
        获取转置的逆
            对于任意 index_ls，有：
                x.transpose(*index_ls).transpose(*reverse_index_ls(index_ls)) == x
            恒成立。

        参数：
            index_ls:   <np.array> 格式具体参考 dimension.coordinates
    """
    r_index_ls = np.empty_like(index_ls)
    r_index_ls[index_ls] = np.arange(len(index_ls))
    return r_index_ls


if __name__ == '__main__':
    import numpy as np

    print(get_inverse_of_transpose_index_ls(index_ls=np.array([0, 4, 1, 5, 2, 3])))
