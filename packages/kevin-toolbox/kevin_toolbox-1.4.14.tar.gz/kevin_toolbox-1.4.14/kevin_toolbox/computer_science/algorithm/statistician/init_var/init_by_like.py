import torch
import numpy as np


def init_by_like(var):
    """
        构建一个与输入 var 具有相同类型、形状、设备的 0 数组

        参数：
            var:                <torch.tensor / np.ndarray / int / float>
    """
    if torch.is_tensor(var):
        res = torch.zeros_like(var)
    elif isinstance(var, (np.ndarray,)):
        res = np.zeros_like(var)
    elif isinstance(var, (int, float, np.number,)):
        res = 0.0
    else:
        raise ValueError("paras 'like' should be np.ndarray, torch.tensor or int/float")
    return res
