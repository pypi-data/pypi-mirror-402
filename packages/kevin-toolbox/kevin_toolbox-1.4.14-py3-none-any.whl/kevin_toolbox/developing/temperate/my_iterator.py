from .my_iterator_base import My_Iterator_Base


class My_Iterator(My_Iterator_Base):
    """
        My_Iterator_Base 的简单实现
    """

    def __init__(self, array):
        assert isinstance(array, (list, tuple,))
        self.array = array
        self.beg, self.end, self.offset = 0, len(self.array), 0

    # ------------------------------------ read ------------------------------------ #

    def read(self, index):
        """
            从 array 中读取对应位置的元素
                根据实际需要来修改，比如添加类型检查、转换等
        """
        return self.array[index]

    # ------------------------------------ iterator ------------------------------------ #

    def __iter__(self):
        return self

    def __next__(self):
        index = self.offset + self.beg
        if index >= self.end:
            raise StopIteration

        v = self.read(index)
        self.offset += 1
        return v

    def set_range(self, beg, end):
        assert 0 <= beg <= end <= len(self.array)
        self.beg = beg
        self.end = end
        self.offset = 0

    def pass_by(self, num):
        self.offset += num

    # ------------------------------------ sequence ------------------------------------ #

    def __getitem__(self, index):
        index = self.__round_by_range(self.beg, self.end, index)
        v = self.read(index)
        return v

    def __len__(self):
        return self.end - self.beg

    # ------------------------------------ else ------------------------------------ #

    def __round_by_range(self, beg, end, offset):
        return super().round_by_range(beg, end, offset)
