import os
import numpy as np
from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register()
class Numpy_Npy(Backend_Base):
    name = ":numpy:npy"

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)

        np.save(os.path.join(self.paras["folder"], f'{name}.npy'), var)
        details = dict(shape=list(var.shape), dtype=f'{var.dtype}')
        return dict(backend=Numpy_Npy.name, name=name, details=details)

    def read(self, name, **kwargs):
        assert self.readable(name=name)

        var = np.load(os.path.join(self.paras["folder"], f'{name}.npy'))
        return var

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        return isinstance(var, (np.generic, np.ndarray))

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return os.path.isfile(os.path.join(self.paras["folder"], f'{name}.npy'))


if __name__ == '__main__':
    print(SERIALIZER_BACKEND.database)
    backend = Numpy_Npy(folder=os.path.join(os.path.dirname(__file__), "temp"))

    a = np.random.randn(100, 2)
    res = backend.write(name=":a:b", var=a)
    print(res)

    b = backend.read(**res)
    print(b)

    print(SERIALIZER_BACKEND.database)
