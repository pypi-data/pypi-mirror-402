from kevin_toolbox.patches.for_matplotlib.color import Color_Format, convert_format
from kevin_toolbox.patches.for_numpy import random

PREDEFINED = ['blue', 'red', 'green', 'orange', 'purple', 'yellow', "brown", "pink", "gray", "olive", "cyan"]
PREDEFINED = [convert_format(var=i, output_format=Color_Format.HEX_STR) for i in PREDEFINED]

population = tuple('0123456789ABCDEF')


def generate_color_list(nums, seed=None, rng=None, exclude_ls=None, output_format=Color_Format.HEX_STR):
    """
        生成颜色列表

        参数:
            nums:           <int> 生成颜色的数量
            seed,rng:       随机种子或随机生成器，二选一
            exclude:        <list of str> 需要排除的颜色
            output_format:  <Color_Format/str> 输出格式
                            支持 HEX_STR、RGBA_ARRAY 两种格式
        返回：
            不包含 alpha 透明度值的颜色列表
    """
    global PREDEFINED, population
    assert output_format in [Color_Format.HEX_STR, Color_Format.RGBA_ARRAY]
    output_format = Color_Format(output_format)
    if exclude_ls is None:
        exclude_ls = []
    assert isinstance(exclude_ls, (list, tuple))
    exclude_ls = set(convert_format(var=i, output_format=Color_Format.HEX_STR) for i in exclude_ls)
    rng = random.get_rng(seed=seed, rng=rng)

    colors = [i for i in PREDEFINED if i not in exclude_ls][:nums]  # 优先输出预定义的颜色

    # 随机生成剩余数量的颜色
    while len(colors) < nums:
        c = "#" + ''.join(
            rng.choice(population, size=6, replace=True))
        if c not in colors and c not in exclude_ls:
            colors.append(c)
    colors = [convert_format(c, output_format=output_format) for c in colors]

    return colors


if __name__ == '__main__':
    color_list = generate_color_list(1, exclude_ls=['blue'])
    print(color_list)

    color_list = generate_color_list(nums=1, seed=114, exclude_ls=['#0000FF'])
    print(color_list)
