def flatten_list(ls, depth=None):
    """
        将列表展平
            比如对于输入 ls=[[1, 2, (3, 4)], [(5,)], 6], depth=None
            展平后得到的输出为 [1, 2, 3, 4, 5, 6]

        参数:
            ls:         <list/tuple> 要展平的列表
            depth:      <int> 展开到第几层
                            0 表示当前层，亦即不作展开
                            默认为 None 表示展开到最深的那层
    """
    assert isinstance(ls, (list, tuple,))
    assert depth is None or isinstance(depth, (int,))
    return _recursion(ls=ls, depth=depth)


def _recursion(ls, depth):
    if depth is not None and depth <= 0:
        res = ls
    else:
        res = []
        for i in ls:
            if isinstance(i, (list, tuple,)):
                res.extend(_recursion(i, depth=depth if depth is None else depth - 1))
            else:
                res.append(i)
    return res


if __name__ == '__main__':
    a = [[1, 2, (3, 4)], [(5,)], 6]
    print(flatten_list(ls=a, depth=None))
