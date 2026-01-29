import torch
import numpy as np


def init_by_data_format(type_, shape, **kwargs):
    """
        构建一个与输入 var 具有相同类型、形状、设备的 0 数组

        参数：
            type_:              <str>
                                    "numpy":        np.ndarray
                                    "torch":        torch.tensor
                                    "number":       float
            shape:              <list of integers>
            device:             <torch.device>
            dtype:              <torch.dtype / np.dtype>
    """
    if type_ == "torch":
        res = torch.zeros(size=shape, **kwargs)
    elif type_ == "numpy":
        res = np.zeros(shape=shape, **kwargs)
    else:
        res = 0.0
    return res
