import os
from abc import ABC, abstractmethod


class Backend_Base(ABC):
    """
        对节点值进行序列化的抽象类

        使用方法：
            若要添加新的<序列化方式>，可以实现一个带有：
                - write(name, var, **kwargs):         序列化
                - read(name, **kwargs):               反序列化
                - writable(var, **kwargs):            是否可以写
                - readable(name, **kwargs):           是否可以读
            等方法的序列化 backend 类，然后将其实例注册到 SERIALIZER_BACKEND 中
    """

    def __init__(self, *args, **kwargs):
        """
            参数：
                folder：         <path> 保存、读取的文件夹
        """

        # 默认参数
        paras = {
            "folder": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(paras["folder"], (str,))
        os.makedirs(paras["folder"], exist_ok=True)

        self.paras = paras

    # ------------------------------------ 读取数据 ------------------------------------ #

    @abstractmethod
    def write(self, name, var, **kwargs):
        """
            序列化
        """
        assert self.writable(var=var)
        return

    @abstractmethod
    def read(self, name, **kwargs):
        """
            反序列化
        """
        assert self.readable(name=name)
        return

    @abstractmethod
    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        return False

    @abstractmethod
    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return False
