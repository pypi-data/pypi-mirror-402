import os
import numpy as np
from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register()
class Numpy_Bin(Backend_Base):
    name = ":numpy:bin"

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)

        var.tofile(os.path.join(self.paras["folder"], f'{name}.bin'))
        details = dict(shape=list(var.shape), dtype=f'{var.dtype}')
        return dict(backend=Numpy_Bin.name, name=name, details=details)

    def read(self, name, **kwargs):
        assert self.readable(name=name)
        details = kwargs["details"]

        var = np.fromfile(os.path.join(self.paras["folder"], f'{name}.bin'))
        var = var.astype(np.dtype(details["dtype"]))
        var.resize(details["shape"])
        return var

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        return type(var) is np.ndarray or isinstance(var, (np.bool_, np.number, np.flexible))

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return os.path.isfile(os.path.join(self.paras["folder"], f'{name}.bin'))


if __name__ == '__main__':
    backend = Numpy_Bin(folder=os.path.join(os.path.dirname(__file__), "temp"))

    a = np.random.randn(100, 2)
    res = backend.write(name=":a:b", var=a)
    print(res)

    b = backend.read(**res)
    print(b)
