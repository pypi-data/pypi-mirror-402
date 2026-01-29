import torch
import numpy as np

FUNCTION_TABLE_GALLERY = dict(
    np_array=dict(
        swapaxes=lambda x, axis_0, axis_1: np.swapaxes(x, axis_0, axis_1),
        permute=lambda x, axis_ls: np.transpose(x, axis_ls),
        concat=lambda x_ls, axis: np.concatenate(x_ls, axis=axis),
        flatten=lambda x, axis_0, axis_1: x.reshape(list(x.shape[:axis_0]) + [-1] + list(x.shape[axis_1 + 1:]))
    ),
    torch_tensor=dict(
        swapaxes=lambda x, axis_0, axis_1: torch.transpose(x, axis_0, axis_1),
        permute=lambda x, axis_ls: x.permute(*axis_ls),
        concat=lambda x_ls, axis: torch.cat(x_ls, dim=axis),
        flatten=lambda x, axis_0, axis_1: torch.flatten(x, start_dim=axis_0, end_dim=axis_1),
    )
)
"""
已注册函数及其使用方法：
    - swapaxes(x, axis_0, axis_1)
    - permute(x, axis_ls)
    - concat(x_ls, axis)
    - flatten(x, axis_0, axis_1)  将 axis_0 到 axis_1 之间的轴进行展平
"""


def get_function_table_for_array_and_tensor(x):
    """
        根据输入 x 的类型获取对应的 function_table
            目前 function_table 已覆盖的函数有：
                swapaxes(x, dim0, dim1)  交换两个维度
                permute(x, dim_ls)  对维度进行重排

        返回：
            [type], [function_table]
    """
    if type(x) is np.ndarray:
        key = "np_array"
    elif torch.is_tensor(x):
        key = "torch_tensor"
    else:
        raise ValueError(f'x should be np.array or torch.tensor, but get a {type(x)}')
    return key, FUNCTION_TABLE_GALLERY[key]
