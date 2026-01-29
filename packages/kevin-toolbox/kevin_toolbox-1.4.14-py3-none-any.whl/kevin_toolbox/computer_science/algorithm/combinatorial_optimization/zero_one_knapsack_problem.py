def zero_one_knapsack_problem(**kwargs):
    """
        使用动态规划求 01 背包
            支持 weights 和 values 是负数的情况

        参数:
            weights:                <list> 可选 item 的“体积”
            values:                 <list> 对应 item 的价值
                                        注意：weights 和 values 中也可以包含负数
            upper_bound:            <int/float> 背包的“容量”上限
                                        注意：upper_bound 也可以是负数
        返回:
            v, idx_ls
            背包可以容纳的最大价值，对应子集的下标序列
                当解不存在时候，返回 None, None
    """
    # 默认参数
    paras = {
        "weights": None,
        "values": None,
        "upper_bound": None,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert paras["weights"] is not None
    assert paras["upper_bound"] is not None
    if paras["values"] is None:
        paras["values"] = paras["weights"]
    assert len(paras["weights"]) == len(paras["values"]) > 0

    return _recursion(weights=paras["weights"], values=paras["values"], upper_bound=paras["upper_bound"],
                      end_idx=len(paras["weights"]) - 1, memory=dict())


def _recursion(weights, values, upper_bound, end_idx, memory):
    if end_idx < 0:
        return (None, None) if upper_bound < 0 else (0, [])
    if (upper_bound, end_idx) in memory:
        return memory[(upper_bound, end_idx)]

    v_0, idx_ls_0 = _recursion(weights=weights, values=values, upper_bound=upper_bound, end_idx=end_idx - 1,
                               memory=memory)
    v_1, idx_ls_1 = _recursion(weights=weights, values=values, upper_bound=upper_bound - weights[end_idx],
                               end_idx=end_idx - 1, memory=memory)
    if v_1 is not None:
        v_1 += values[end_idx]
        idx_ls_1 = idx_ls_1 + [end_idx]

    if v_0 is None:
        res = (v_1, idx_ls_1)
    elif v_1 is None:
        res = (v_0, idx_ls_0[:])
    else:
        res = (v_0, idx_ls_0[:]) if v_0 >= v_1 else (v_1, idx_ls_1)

    memory[(upper_bound, end_idx)] = res

    return res


if __name__ == '__main__':
    # print(zero_one_knapsack_problem(weights=[3, -1, 6, 5, 4], values=[1, 1, 1, 1, 1], upper_bound=7))
    # print(zero_one_knapsack_problem(weights=[-3, -1, -6, -5, -4], upper_bound=7))
    # print(zero_one_knapsack_problem(weights=[0, -3, 3], values=[0, 0, 5], upper_bound=2))
    # print(zero_one_knapsack_problem(weights=[3., 3., 3.], upper_bound=6.338211323106079))
    print(zero_one_knapsack_problem(weights=[0, -5, 3, 0, -1, 3], values=[0, -3, -4, -1, -2, 2], upper_bound=-7))
    print(zero_one_knapsack_problem(weights=[1.2, 0.4, 2, 2, 2, 2, 2, 2, 2, 2], upper_bound=5))
