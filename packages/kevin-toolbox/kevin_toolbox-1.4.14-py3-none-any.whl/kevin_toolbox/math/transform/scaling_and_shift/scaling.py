def scaling(**kwargs):
    """
        以给定的 zero_point 为原点，将 x 以 factor 为比例进行放大/缩小
            由于数值计算过程存在截断误差，本函数在同样的 factor,zero_point 配置下进行正向和逆向运算时，仅能保证 1e-2 之前的数值相同。

        必要参数：
            x:              <torch.tensor/np.array>
            factor:         <int/float>
            zero_point:     <int/float>
            reverse:        <boolean> 逆操作

        建议：
            - 对于需要保留更多小数点后精度的情况，建议在输入前先进行一定比例的放大。
    """

    # 默认参数
    paras = {
        # 必要参数
        "x": None,
        #
        "factor": 1,
        "zero_point": 0,
        "reverse": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert paras["x"] is not None
    x = paras["x"]
    for key in {"factor", "zero_point"}:
        assert isinstance(paras[key], (int, float,))
    assert paras["factor"] > 0
    factor, zero_point = paras["factor"], paras["zero_point"]

    if not paras["reverse"]:
        y = (x - zero_point) * factor + zero_point
    else:
        y = (x - zero_point) / factor + zero_point

    return y
