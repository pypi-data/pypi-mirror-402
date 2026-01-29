import os
import torch
from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register()
class Torch_All(Backend_Base):
    name = ":torch:all"

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)

        torch.save(var, os.path.join(self.paras["folder"], f'{name}.pth'))
        return dict(backend=Torch_All.name, name=name)

    def read(self, name, **kwargs):
        assert self.readable(name=name)

        return torch.load(os.path.join(self.paras["folder"], f'{name}.pth'))

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        return True

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return os.path.isfile(os.path.join(self.paras["folder"], f'{name}.pth'))


if __name__ == '__main__':
    print(SERIALIZER_BACKEND.database)
    backend = Torch_All(folder=os.path.join(os.path.dirname(__file__), "temp"))

    var_ = dict(a=torch.randn(100, device=torch.device("cuda")), b=torch.randn(100, device=torch.device("cpu")))
    print(backend.write(name=":inst", var=var_))

    b = backend.read(name=":inst")
    print(b)
