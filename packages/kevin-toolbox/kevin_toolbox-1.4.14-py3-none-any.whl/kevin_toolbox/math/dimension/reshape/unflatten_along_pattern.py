import numpy as np
from kevin_toolbox.math.dimension import coordinates, transpose


def unflatten_along_pattern(**kwargs):
    """
        将 x 最后的一个维度，按照 shape 对应的 generate_func 指定的遍历顺序进行堆叠
            实际上就是打平展开 flatten_along_pattern() 的逆向操作

        参数：
            x：                  <nparray/tensor>
            shape：              <list/tuple of integers>
            generate_func：      用于指定对 block 的遍历顺序
                                    默认使用 coordinates.generate(pattern="z_pattern", output_format="index_ls") 进行遍历
                                    你也可以自定义一个根据参数 shape 生成 zip_indices 格式的坐标列表的函数，来指定遍历顺序
    """
    # 默认参数
    paras = {
        # 必要参数
        "x": None,
        "shape": None,
        "generate_func": lambda shape: coordinates.generate(pattern="z_pattern", output_format="index_ls",
                                                            shape=shape),
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert paras["x"] is not None
    x = paras["x"]
    assert isinstance(paras["shape"], (list, tuple,)) and np.prod(paras["shape"]) == x.shape[-1], \
        f'type {type(paras["shape"])} in [list, tuple] ? {np.prod(paras["shape"])} == {x.shape[-1]}？'
    shape = paras["shape"]
    # generate_func
    assert callable(paras["generate_func"])

    # 获取转置的逆
    index_ls = paras["generate_func"](shape=shape)
    r_index_ls = transpose.get_inverse_index_ls(index_ls)

    # 对最后的维度进行转置
    y = transpose.inside_axis(x=x, axis=-1, index_ls=r_index_ls)

    # reshape
    new_shape = list(y.shape)[:-1] + list(shape)
    y = y.reshape(new_shape)

    return y
