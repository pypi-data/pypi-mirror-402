import os
from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND
from kevin_toolbox.nested_dict_list.serializer import write, read


@SERIALIZER_BACKEND.register()
class NDL(Backend_Base):
    name = ":ndl"

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)

        write(var=var, output_dir=os.path.join(self.paras["folder"], f'{name}'),
              settings=None, traversal_mode="bfs", b_pack_into_tar=False, **kwargs)
        return dict(backend=NDL.name, name=name)

    def read(self, name, **kwargs):
        assert self.readable(name=name)

        input_path = os.path.join(self.paras["folder"], f'{name}.tar') if os.path.isfile(
            os.path.join(self.paras["folder"], f'{name}.tar')) else os.path.join(self.paras["folder"], f'{name}')

        return read(input_path=input_path, **kwargs)

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        if "name" in kwargs:
            return not os.path.exists(os.path.join(self.paras["folder"], f'{kwargs["name"]}'))
        else:
            return True

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        res = os.path.isfile(os.path.join(self.paras["folder"], f'{name}.tar')) or \
              os.path.isdir(os.path.join(self.paras["folder"], f'{name}'))
        return res


if __name__ == '__main__':
    import torch

    backend = NDL(folder=os.path.join(os.path.dirname(__file__), "temp"))

    a = {"a": 1, "b": [torch.randn(100, device=torch.device("cuda"))]}
    print(backend.write(name=":a:b", var=a))

    b = backend.read(name=":a:b")
    print(b)

    print(SERIALIZER_BACKEND.database)
