import torch
from kevin_toolbox.env_info import version

"""
    在 1.8 及其以下版本的 pytorch 中，没有 torch.linalg.svd()
        改用 torch.svd() 来实现，
        实现过程中考虑到两者的输出的 V 矩阵发生了转置，同时输入的 full_matrices 与 some 互为反义
"""

if version.compare(torch.__version__, "<=", "1.8", mode="short"):
    @torch.no_grad()
    def svd(X, full_matrices=True):
        U, S, V = torch.svd(X, some=not full_matrices)
        V = V.transpose(-2, -1)
        return U, S, V
else:
    svd = torch.linalg.svd
