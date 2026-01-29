def set_crop_by_box(x, box_ls, crop_ls, beg_axis=0):
    """
        将 crop_ls 填充到 x 中 boxes 指定的区域
            将直接在输入的 x 上进行 inplace 赋值操作

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
            crop_ls:        <list of np.array/tensor> 需要与 boxes 一一对应
            beg_axis:       <integer> 上面提供的 boxes 中指定的坐标是从 x/crop 的第几个 axis 开始对应的。
                                例如： beg_axis=1 时，box=[[i,j],[m,n]] 表示该 crop 是从原张量的 x[:, i:m, j:n, ...] 部分截取出来的。

        返回：
            x:              <np.array/tensor>
    """
    assert isinstance(box_ls, (list,)) and len(box_ls) > 0
    assert isinstance(beg_axis, (int,)) and 0 <= beg_axis <= x.ndim - box_ls[0].shape[-1], \
        f'0 <= {beg_axis} <= {x.ndim - box_ls[0].shape[-1]} ?'
    assert isinstance(crop_ls, (list,)) and len(crop_ls) == len(box_ls)

    for crop, box in zip(crop_ls, box_ls):
        x[tuple([slice(None, None)] * beg_axis + [slice(beg, end) for beg, end in zip(box[0], box[1])])] = crop

    return x
