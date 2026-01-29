import os
import torch
from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register()
class Torch_Tensor(Backend_Base):
    name = ":torch:tensor"

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)

        torch.save(var, os.path.join(self.paras["folder"], f'{name}.pt'))
        details = dict(shape=list(var.shape), device=var.device.type, dtype=f'{var.dtype}')
        return dict(backend=Torch_Tensor.name, name=name, details=details)

    def read(self, name, **kwargs):
        assert self.readable(name=name)

        return torch.load(os.path.join(self.paras["folder"], f'{name}.pt'))

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        return torch.is_tensor(var)

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return os.path.isfile(os.path.join(self.paras["folder"], f'{name}.pt'))


if __name__ == '__main__':
    backend = Torch_Tensor(folder=os.path.join(os.path.dirname(__file__), "temp"))

    a = torch.randn(100, device=torch.device("cuda"))
    print(backend.write(name=":a:b", var=a))

    b = backend.read(name=":a:b")
    print(b)

    print(SERIALIZER_BACKEND.database)
