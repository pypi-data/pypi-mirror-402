import torch
from kevin_toolbox.env_info import version

"""
    参考 torch.concat()
        在 1.9 版本及其之前的 pytorch 中没有 torch.concat()，
        而只有 torch.cat()，
        两者用法与效果一致， concat 可以看做 cat 的别名
"""

if version.compare(torch.__version__, "<", "1.10", mode="short"):
    concat = torch.cat
else:
    concat = torch.concat
