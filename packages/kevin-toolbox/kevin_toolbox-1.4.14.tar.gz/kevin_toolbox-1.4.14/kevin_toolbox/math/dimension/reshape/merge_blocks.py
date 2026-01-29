from kevin_toolbox.math import utils


def merge_blocks(x, block_axis_num):
    """
        将最后 block_axis_num 个维度看做是 block，合并到此前 axis_num 个维度上。
            是 split_blocks() 的逆操作。

        参数：
            x:                  <np.array>
            block_axis_num:     <integer> 维度数量
    """

    # 校验参数
    _, function_table = utils.get_function_table_for_array_and_tensor(x)
    permute = function_table["permute"]
    assert isinstance(block_axis_num, (int,))
    assert x.ndim >= 2 * block_axis_num > 0

    offset = x.ndim - 2 * block_axis_num
    new_shape = list(x.shape[:offset])
    new_axis = list(range(offset))
    for i, (b, k) in enumerate(zip(x.shape[-2 * block_axis_num:-block_axis_num], x.shape[-block_axis_num:])):
        new_shape.append(b * k)
        new_axis.append(offset + i)
        new_axis.append(offset + i + block_axis_num)

    # x: [b, b0, b1, k0, k1] ==> [b, b0, k0, b1, k1] ==> [b, b0*k0, b1*k1]
    y = permute(x, new_axis).reshape(new_shape)
    return y
