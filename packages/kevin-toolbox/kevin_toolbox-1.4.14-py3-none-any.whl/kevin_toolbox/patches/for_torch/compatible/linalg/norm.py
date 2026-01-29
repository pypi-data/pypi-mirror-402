import torch
from kevin_toolbox.env_info import version

"""
    在 1.8 及其以下版本的 pytorch 中，没有 torch.linalg.norm()
        改用 torch.norm() 来实现，
        但是需要注意两者的输出并非完全一致，会有一定的偏差，但非常微小（在1e-10的量级）
"""

if version.compare(torch.__version__, "<=", "1.8", mode="short"):
    _arg_name_ls = [None, "ord", "dim", "keepdim", "out", "dtype"]


    def norm(*args, **kwargs):
        if len(args) > 0:
            X = args[0]
            for name, arg in zip(_arg_name_ls[1:len(args)], args[1:]):
                kwargs[name] = arg
            args = [X]
        kwargs["p"] = kwargs.pop("ord")
        return torch.norm(*args, **kwargs)
else:
    norm = torch.linalg.norm
