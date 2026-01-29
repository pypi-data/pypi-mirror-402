"""数据集生成器"""


def build_generator(executor_ls, size_ls=None):
    """
        根据 executor_ls 构建数据集的生成器

        参数：
            executor_ls：        执行器列表
            size_ls：            数据集大小
                                    当为非空时，将根据 size_ls 对 executor 实际上生成数据集的大小进行检查
        返回：
            generator：          一个产生 dataset 的生成器
    """
    assert isinstance(executor_ls, (list, tuple,))
    if size_ls is not None:
        assert isinstance(size_ls, (list, tuple,)) and len(size_ls) == len(executor_ls)

    def generator():
        for i, executor in enumerate(executor_ls):
            res = executor()
            if size_ls is None:
                assert len(res[list(res.keys())[0]]) == size_ls[i]
            yield res

    return generator()
