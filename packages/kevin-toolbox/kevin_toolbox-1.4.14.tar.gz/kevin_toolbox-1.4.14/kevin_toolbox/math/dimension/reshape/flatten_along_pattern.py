from kevin_toolbox.math.dimension import coordinates
from kevin_toolbox.math import utils


def flatten_along_pattern(**kwargs):
    """
        将 x 的最后 dim_num 个维度按照 generate_func 指定的遍历顺序进行打平展开

        参数：
            x：                  <np.array/tensor>
            dim_num：            <integer>
            generate_func：      用于指定对 block 的遍历顺序
                                    默认使用 coordinates.generate(pattern="z_pattern", output_format="zip_indices") 进行遍历
                                    你也可以自定义一个根据参数 shape 生成 zip_indices 格式的坐标列表的函数，来指定遍历顺序
    """
    # 默认参数
    paras = {
        # 必要参数
        "x": None,
        "dim_num": None,
        "generate_func": lambda shape: coordinates.generate(pattern="z_pattern", output_format="zip_indices",
                                                            shape=shape),
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    _, function_table = utils.get_function_table_for_array_and_tensor(paras["x"])
    permute = function_table["permute"]
    x = paras["x"]
    assert isinstance(paras["dim_num"], (int,)) and 1 < paras["dim_num"] <= len(x.shape)
    dim_num = paras["dim_num"]
    # generate_func
    assert callable(paras["generate_func"])

    # 首先将 y 要被展开的维度提前
    # y: [64, 8, 4] ==> [8, 4, 64]
    dim_ls = list(range(len(x.shape)))
    dim_ls = dim_ls[-dim_num:] + dim_ls[:-dim_num]
    y = permute(x, dim_ls)

    # 按照指定 pattern 生成的 indices_ls 进行展开
    # y: [8, 4, 64] ==> [32, 64]
    indices = paras["generate_func"](shape=x.shape[-dim_num:])
    y = y[indices]

    # 恢复维度顺序
    # y: [32, 64] ==> [64, 32]
    dim_ls = list(range(len(y.shape)))
    dim_ls = dim_ls[1:] + [0]
    y = permute(y, dim_ls)

    return y
