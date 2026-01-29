def get_crop_by_box(x, box_ls, beg_axis=0):
    """
        根据 boxes/box_ls 选定的区域，将 crop_ls 从源张量 x 中截取出来。

        参数：
            x:              <np.array/tensor>
            box_ls:         <list of box>
                                each box is a np.array with shape [batch_size, 2, dimensions]，各个维度的意义为：
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
                                要求：
                                    - 各个 box 应该是已经 sorted 的，亦即小坐标在前大坐标在后。
                                        例如 box=[[1,2],[0,4]] 是错误的。
                                        而 box=[[0,2],[1,4]] 是合法的。
            beg_axis:       <integer> 上面提供的 boxes 中指定的坐标是从 x/crop 的第几个 axis 开始对应的。
                                例如： beg_axis=1 时，box=[[i,j],[m,n]] 表示该 crop 是从原张量的 x[:, i:m, j:n, ...] 部分截取出来的。

        返回：
            crop_ls:        <list of np.array/tensor>
    """
    assert isinstance(box_ls, (list,)) and len(box_ls) > 0
    assert isinstance(beg_axis, (int,)) and 0 <= beg_axis <= x.ndim - box_ls[0].shape[-1], \
        f'0 <= {beg_axis} <= {x.ndim - box_ls[0].shape[-1]} ?'

    # 根据 box 从 x 中截取 crop
    crop_ls = [x[tuple(
        [slice(None, None)] * beg_axis + [slice(beg, end) for beg, end in zip(box[0], box[1])]
    )] for box in box_ls]

    return crop_ls
