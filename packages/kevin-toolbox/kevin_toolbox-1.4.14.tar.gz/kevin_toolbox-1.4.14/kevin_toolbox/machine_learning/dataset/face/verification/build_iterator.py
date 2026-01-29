from kevin_toolbox.developing.temperate import My_Iterator
from kevin_toolbox.computer_science.data_structure import Executor


def build_iterator(executor_ls, size_ls=None):
    """
        根据 executor_ls 构建数据集的迭代器

        参数：
            executor_ls：        执行器列表
            size_ls：            数据集大小
                                    当为非空时，将根据 size_ls 对 executor 实际上生成数据集的大小进行检查
        返回：
            iterator：          一个产生 dataset 的迭代器
    """
    return Iterator_for_Executor_ls(executor_ls, size_ls)


class Iterator_for_Executor_ls(My_Iterator):
    """
        根据 executor_ls 构建迭代器
            支持的功能参见 My_Iterator_Base：
                支持 iter(self) 迭代
                    self.set_range(beg,end) 设定迭代起点、终点
                    self.pass_by(num)    跳过若干个值
                支持 self[index] 取值、len(self) 获取长度属性

        参数：
            executor_ls：        执行器列表
            size_ls：            数据集大小
                                    当为非空时，将根据 size_ls 对 executor 实际上生成数据集的大小进行检查
    """

    def __init__(self, executor_ls, size_ls=None):
        super().__init__(executor_ls)  # 在父类方法中， self.array = executor_ls

        if size_ls is not None:
            assert isinstance(size_ls, (list, tuple,)) and len(size_ls) == len(self.array)
        self.size_ls = size_ls

    def read(self, index):
        executor = self.array[index]
        assert isinstance(executor, (Executor,))

        res = executor()
        if self.size_ls is not None:
            assert len(res[list(res.keys())[0]]) == self.size_ls[index]
        return res
