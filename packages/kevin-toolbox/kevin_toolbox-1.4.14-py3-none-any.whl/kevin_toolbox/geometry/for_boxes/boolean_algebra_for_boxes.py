import os
import numpy as np
from kevin_toolbox.geometry import for_boxes
from kevin_toolbox.math.dimension import coordinates

U_OPERATION_CHOICES = {None, "not"}
BI_OPERATION_CHOICES = {'or', 'and', 'diff'}


def boolean_algebra_for_boxes(**kwargs):
    """
        布尔运算
            对 boxes_ls 中的各个 boxes，按照 binary_operation_ls、unary_operation_ls 中指定的操作进行布尔运算

        参数：
            boxes_ls:          <list of boxes/None>
                                where boxes is <np.array> with shape [batch, 2, dimensions]
                                各个维度的意义为：
                                    batch：      box的数量
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
                                where None represents the empty set
            binary_operation_ls:    <list of string> 二元运算操作（对两个相邻的 box进行操作）
                                支持以下运算符：
                                    "and":      与
                                    "or":       或
                                    "diff":     减去， a diff b 等效于 a and (not b)
                                注意：
                                    - 因为二元运算符是对两个 box 进行操作的，因此 binary_operation_ls 的长度需要比 boxes_ls 小 1
            unary_operation_ls:     <list> 一元运算符
                                支持以下运算符：
                                    "not":      取反
                                    None:       不进行运算
                                默认为 None，表示不进行任何一元运算
                                注意：
                                    - 当 unary_operation_ls 设定有具体值时，要求其长度与 boxes_ls 相等
                                    - ！！当使用 "not" 运算时，默认使用 boxes_ls 的最小外切长方体作为全集。
                                        如果要指定全集 U 的范围，建议在第一个元素 a 前添加操作 U and a，
                                        该操作将显式地声明全集范围。
        返回：
            boxes 当结果为空集时，返回 None
    """
    # 默认参数
    paras = {
        # 必要参数
        "boxes_ls": None,
        "binary_operation_ls": None,
        "unary_operation_ls": None,
    }

    # 获取参数
    paras.update(kwargs)
    global U_OPERATION_CHOICES, BI_OPERATION_CHOICES

    # 校验参数
    assert isinstance(paras["boxes_ls"], (list,))
    boxes_ls = paras["boxes_ls"]
    if len(boxes_ls) == 0:
        return None
    # ticks
    temp = [boxes for boxes in boxes_ls if boxes is not None]
    if len(temp) == 0:
        return None
    elif len(temp) > 1:
        temp = np.concatenate(temp, axis=0).astype(dtype=np.float32)
    else:
        temp = temp[0]
    ticks = for_boxes.get_ticks(boxes=temp)
    #
    if paras["unary_operation_ls"] is None:
        paras["unary_operation_ls"] = [None] * len(boxes_ls)
    paras["binary_operation_ls"].insert(0, "or")  # 添加哨兵
    #
    for key, choices in zip(["unary_operation_ls", "binary_operation_ls"], [U_OPERATION_CHOICES, BI_OPERATION_CHOICES]):
        assert len(paras[key]) == len(boxes_ls)
        assert set(paras[key]).issubset(choices), \
            f'ele in {key} should be string in {choices}, but get {set(paras[key])}'
    unary_operation_ls = paras["unary_operation_ls"]
    binary_operation_ls = paras["binary_operation_ls"]

    # convert to grid
    settings_for_grid = dict(mode="closed", ticks=ticks)
    grids_ls = []
    for boxes in boxes_ls:
        if boxes is None:
            grids_ls.append(None)
        else:
            grids_ls.append(
                for_boxes.convert_from_coord_to_grid_index(boxes=boxes, settings_for_grid=settings_for_grid))

    # convert to matrix
    grid_shape = [len(tk_ls) - 1 for tk_ls in ticks]
    res_matrix = np.zeros(shape=grid_shape, dtype=bool)
    for i, grids in enumerate(grids_ls):
        bi_operation = binary_operation_ls[i]
        u_operation = unary_operation_ls[i]
        #
        matrix = np.zeros(shape=grid_shape, dtype=bool)
        if grids is not None:
            for grid in grids:
                scope = ','.join([f"{int(beg)}:{int(end)}" for beg, end in zip(grid[0], grid[1])])
                exec(f"matrix[{scope}]=1")
        #
        if u_operation is None:
            pass
        elif u_operation == "not":
            matrix = ~matrix
        else:
            raise ValueError
        #
        if bi_operation == "or":
            res_matrix = res_matrix | matrix
        elif bi_operation == "and":
            res_matrix = res_matrix & matrix
        elif bi_operation == "diff":  # a diff b == a and (not b)
            res_matrix = res_matrix & ~matrix
        else:
            raise ValueError

    # pick result from matrix
    zip_indices = np.where(res_matrix)
    indices_ls = coordinates.convert(var=zip_indices, shape=res_matrix.shape,
                                     input_format="zip_indices", output_format="indices_ls")
    # convert back to box_ls
    res_boxes = None
    if len(indices_ls) > 0:
        beg = indices_ls.reshape(indices_ls.shape[0], 1, -1)
        end = beg + 1
        res_grids = np.concatenate([beg, end], axis=1)
        res_boxes = for_boxes.convert_from_coord_to_grid_index(boxes=res_grids, settings_for_grid=settings_for_grid,
                                                               reverse=True)
    return res_boxes
