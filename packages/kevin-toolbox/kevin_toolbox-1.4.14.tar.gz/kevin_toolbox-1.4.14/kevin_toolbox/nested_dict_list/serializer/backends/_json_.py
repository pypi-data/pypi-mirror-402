import os
from kevin_toolbox.data_flow.file import json_
from kevin_toolbox.nested_dict_list.serializer.backends import Backend_Base
from kevin_toolbox.nested_dict_list.serializer.variable import SERIALIZER_BACKEND


@SERIALIZER_BACKEND.register()
class Json_(Backend_Base):
    name = ":json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.w_cache = None
        self.w_cache_s = dict(able=None, id_=None, content=None)

    def write(self, name, var, **kwargs):
        assert self.writable(var=var)

        with open(os.path.join(self.paras["folder"], f'{name}.json'), "w") as f:
            f.write(self.w_cache_s["content"])

        self.w_cache_s["content"], self.w_cache_s["id_"] = None, None
        return dict(backend=Json_.name, name=name)

    def read(self, name, **kwargs):
        assert self.readable(name=name)

        var = json_.read(file_path=os.path.join(self.paras["folder"], f'{name}.json'), b_use_suggested_converter=True)
        return var

    def writable(self, var, **kwargs):
        """
            是否可以写
        """
        if id(var) != self.w_cache_s["id_"]:
            try:
                self.w_cache_s["content"] = json_.write(content=var, file_path=None, b_use_suggested_converter=True,
                                                        output_format=kwargs.get("output_format", "pretty_printed"))
            except:
                self.w_cache_s["content"], self.w_cache_s["id_"] = None, None
                self.w_cache_s["able"] = False
            else:
                self.w_cache_s["id_"] = None
                self.w_cache_s["able"] = True
        return self.w_cache_s["able"]

    def readable(self, name, **kwargs):
        """
            是否可以写
        """
        return os.path.isfile(os.path.join(self.paras["folder"], f'{name}.json'))


if __name__ == '__main__':
    backend = Json_(folder=os.path.join(os.path.dirname(__file__), "temp"))

    var_ = [{123: 123, None: None, "<eval>233": 233, "foo": (2, 3, 4)}, 233]
    # backend.writable(var=var_)
    print(backend.write(name=":inst", var=var_))

    b = backend.read(name=":inst")
    print(b)
