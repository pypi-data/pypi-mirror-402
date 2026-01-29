from kevin_toolbox.math import utils


def split_blocks(x, block_shape):
    """
        将最后部分的维度 axis 按照 block_shape 分割成 blocks 的组成
            例如，对于 x=[5, 6, 6]，在 block_shape=[3, 2] 的情况下将得到 y=[5, 2, 3, 3, 2]

        参数：
            x:                  <np.array>
            block_shape:        <list/tuple> block 的形状
    """

    # 校验参数
    _, function_table = utils.get_function_table_for_array_and_tensor(x)
    permute = function_table["permute"]
    assert isinstance(block_shape, (tuple, list,))
    assert x.ndim >= len(block_shape)

    new_shape = list(x.shape[:x.ndim - len(block_shape)])
    axis_ids_for_group, axis_ids_for_block = [], []
    for i, j in zip(x.shape[-len(block_shape):], block_shape):
        assert i >= j and i % j == 0
        new_shape.append(i // j)
        axis_ids_for_group.append(len(new_shape) - 1)
        new_shape.append(j)
        axis_ids_for_block.append(len(new_shape) - 1)
    new_axis = list(range(x.ndim - len(block_shape))) + axis_ids_for_group + axis_ids_for_block

    # x: [b, w, h] ==> [b, w/k0, k0, h/k1, k1] ==> [b, w/k0, h/k1, k0, k1]
    y = permute(x.reshape(new_shape), new_axis)
    return y
