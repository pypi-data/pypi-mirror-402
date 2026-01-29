def _recursive(indices, axis_beg, axis_end, step, shape):
    if axis_beg == axis_end:  # 到达最后一维
        for i in range(shape[axis_beg]):
            indices[axis_beg] = i
            yield indices
    else:
        for i in range(shape[axis_beg]):
            indices[axis_beg] = i
            yield from _recursive(indices, axis_beg + step, axis_end, step, shape)


def normal_indices_generator(shape, order="C"):
    """
        迭代生成遍历 shape 所需要的所有的坐标 indices
            indices 格式的具体定义参见 coordinates.convert()
        
        参数：
            shape:          <list/tuple> 要遍历的形状
            order:          <str> 遍历的模式
                                两种取值：
                                    "C":    row first，从前往后，首先遍历第一个维度
                                    "F":    column first，从后往前，首先遍历最后一个维度
    """
    assert isinstance(shape, (list, tuple,)) and len(shape) > 0
    assert order in ["C", "F"]

    if order == "C":
        axis_beg, axis_end = 0, len(shape) - 1
        step = 1
    else:
        axis_end, axis_beg = 0, len(shape) - 1
        step = -1

    for indices in _recursive(indices=[0] * len(shape), axis_beg=axis_beg, axis_end=axis_end, step=step, shape=shape):
        yield indices[:]
