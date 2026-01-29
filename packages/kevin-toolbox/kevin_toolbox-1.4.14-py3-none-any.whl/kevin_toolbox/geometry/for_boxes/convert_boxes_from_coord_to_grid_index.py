import numpy as np


def convert_boxes_from_coord_to_grid_index(**kwargs):
    """
        对输入的 boxes，进行 实数坐标 与 网格点序号坐标 之间的坐标转换
            注意：
            - 这种转换可能是可逆的， 实数坐标 ==> 网格点序号坐标 的转换一般会使得 box 的实际范围扩大。
            - 特别地，当使用 grid_coverage_mode=closed 模式，并配合从 boxes 中获取的坐标（可以通过for_boxes.get_ticks()获取）时，
                转换是完全可逆的。
            - 网格点的 index 包头不包尾， beg, end = 0, 1 表示 0 号网格。

        参数：
            boxes:          <3 axis np.array> 需要转换的 box
                                shape [batch_size, 2, dimensions]，各个维度的意义为：
                                    batch_size： 有多少个 box
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
            settings_for_grid:      <dict of paras> 用于设定网格位置、范围的参数列表。
                                目前支持两种格点覆盖模式 mode：
                                    mode:     <string> 格点覆盖模式
                                        支持以下两种模式：
                                            "open"：     开放式，将构建一个覆盖整个空间的格点阵列。
                                            "closed"：   封闭式，仅在指定范围内构建格点阵列。对于超出范围外的坐标，将投影到格点阵列的边界上。
                                在不同的格点覆盖模式 mode 下，有不同的设置方式。
                                目前支持以下三种方式：
                                    mode=open，以 grid_size 为基准
                                        grid_size:      <list/integer/float> 各个维度上网格的大小
                                                            设置为单个 integer 时，默认所有维度使用同一大小的网格划分
                                        offset：         <list/integer/float> 网格点的原点相对于原始坐标的偏移量
                                                            默认为 [0,...]，无偏移
                                                            设置为单个 integer 时，默认所有维度使用同一大小的 offset
                                            例子：
                                                当 grid_size=[1,5] , offset=[3,1]，
                                                表示以 coord=(3,1) 为原点，对维度dim=0以size=1划分网格，对dim=1以size=5划分网格。
                                    mode=closed，以 ticks 为基准
                                        ticks：          <list of np.array> 在各个维度下，网格点的划分坐标
                                                            ticks[i][0] 就是网格的原点坐标，与上面的 offset 相同
                                    mode=closed，以 grid_size 为基准
                                        grid_size:      <list of np.array/list> 在各个维度下，网格点的一系列划分大小
                                        offset：         <list/integer>
                                            函数将会首先把 grid_size 和 offset 转换为对应的 ticks，然后再按照 ticks 执行划分。
            reverse:        <boolean> 决定转换的方向
                                默认为 False，此时为 coord ==> grid_index
                                True 时为 grid_index ==> coord
    """

    # 默认参数
    paras = {
        # 必要参数
        "boxes": None,
        # 格点划分方式
        "grid_coverage_mode": "open",
        "settings_for_grid": None,
        #
        "reverse": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    # boxes
    paras["boxes"] = np.asarray(paras["boxes"], dtype=np.float32)
    assert paras["boxes"].ndim == 3 and paras["boxes"].shape[1] == 2
    boxes = np.sort(paras["boxes"], axis=1)
    # grid
    assert isinstance(paras["settings_for_grid"], (dict,))
    settings = paras["settings_for_grid"]
    assert settings["mode"] in ["open", "closed"]
    mode = settings["mode"]
    # 基础检查
    if "offset" not in settings:
        settings["offset"] = 0
    for key in settings.keys():
        if key in ["grid_size", "offset"]:
            if isinstance(settings[key], (int, float,)):
                settings[key] = [settings[key]] * boxes.shape[-1]
        #
        if key not in ["mode"]:
            assert isinstance(settings[key], (list,)) and boxes.shape[-1] == len(settings[key])
    # 结合 mode 进行检查
    if mode == "open":
        for key in ["grid_size", "offset"]:
            assert key in settings and isinstance(settings[key][0], (int, float,))
    else:
        if "ticks" in settings:
            # convert to np.array
            for i, tk_ls in enumerate(settings["ticks"]):
                settings["ticks"][i] = np.asarray(tk_ls)
            # from ticks get offset
            settings["offset"] = []
            for tk_ls in settings["ticks"]:
                settings["offset"].append(tk_ls[0])
            # from ticks get grid_size
            settings["grid_size"] = []
            for ot, tk_ls in zip(settings["offset"], settings["ticks"]):
                temp = tk_ls - ot
                gd = temp[1:] - temp[:-1]
                settings["grid_size"].append(gd)
        else:
            for key in ["grid_size", "offset"]:
                assert key in settings
            assert not isinstance(settings["grid_size"][0], (int, float,))
            # from grid_size,offset get ticks
            settings["ticks"] = []
            for ot, gd_ls in zip(settings["offset"], settings["grid_size"]):
                tk_ls = np.zeros(shape=len(gd_ls) + 1)
                tk_ls[0] = ot
                tk_ls[1:] = gd_ls
                tk_ls = np.cumsum(tk_ls)
                settings["ticks"].append(tk_ls)

    if mode == "open":
        grid_size, offset = settings["grid_size"], np.asarray(settings["offset"])
        if not paras["reverse"]:
            boxes = boxes - offset
            boxes = boxes / grid_size
            boxes[:, 0, :] = np.floor(boxes[:, 0, :])
            boxes[:, 1, :] = np.ceil(boxes[:, 1, :])
            boxes = boxes.astype(np.int32)
        else:
            boxes = boxes * grid_size
            boxes = boxes + offset
    else:
        grid_size, ticks = settings["grid_size"], settings["ticks"]
        if not paras["reverse"]:
            temp_ls = []
            for dim in range(boxes.shape[-1]):
                temp = boxes[..., [dim]] - ticks[dim].reshape(1, -1)
                temp[..., :-1] = temp[..., :-1] / grid_size[dim]
                #
                temp[:, 0, :] = np.floor(temp[:, 0, :])
                temp[:, 1, :] = np.ceil(temp[:, 1, :])
                #
                temp = np.maximum(np.minimum(temp, 1), 0)
                temp = np.sum(temp, axis=-1, keepdims=True)
                temp_ls.append(temp)
            boxes = np.concatenate(temp_ls, axis=-1)
            boxes = boxes.astype(np.int32)
        else:
            temp = np.zeros_like(boxes)
            for i in range(boxes.shape[0]):
                for j in range(boxes.shape[1]):
                    for dim in range(boxes.shape[-1]):
                        temp[i, j, dim] = ticks[dim][int(boxes[i, j, dim])]
            boxes = temp

    return boxes


if __name__ == '__main__':
    settings_for_grid = dict(mode="open", grid_size=2, offset=1)
    grids = convert_boxes_from_coord_to_grid_index(boxes=np.array([[[1, 3, 4, ],
                                                                    [2, 1, -6]]]),
                                                   settings_for_grid=settings_for_grid)
    print(grids)
    boxes_ = convert_boxes_from_coord_to_grid_index(boxes=grids, settings_for_grid=settings_for_grid,
                                                    reverse=True, )
    print(boxes_)
