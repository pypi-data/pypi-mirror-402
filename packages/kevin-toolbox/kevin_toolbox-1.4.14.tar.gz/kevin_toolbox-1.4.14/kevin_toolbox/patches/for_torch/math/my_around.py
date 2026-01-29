import torch


def my_around(x, decimals, inplace=True, floor=False):
    """
        保留到指定的小数位数。（类似于 np.around() 函数）
        round/floor to the given number of decimals.

        参数：
            x:                  input tensor
            decimals:           要保留的小数位数
        可选参数：
            floor：              采用四舍五入还是直接截取
                                    True：   直接截取
                                    False：  四舍五入
                                    默认为 False
            inplace：            boolean，是否直接在原 tensor 上进行操作
                                    默认为 True
                                    对于 requires_grad=True 的情况，此参数固定为 False
    """
    assert isinstance(decimals, (int,)) and decimals >= 0
    assert isinstance(x, torch.Tensor)

    if not inplace or x.requires_grad:
        x = x.clone()

    scale = 10 ** decimals
    x *= scale
    if floor:
        x.floor_()
    else:
        x.round_()
    x /= scale
    return x


if __name__ == '__main__':
    a = torch.Tensor([1, 2.4342, 8.1234567])
    for inplace in [False, True]:
        a_r = my_around(a, decimals=3, inplace=inplace)
        print(f"value a {a} a_r {a_r}")
        print(f"id a {id(a)} a_r {id(a_r)}")
