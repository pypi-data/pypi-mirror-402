import numpy as np


def cal_iou_between_boxes(**kwargs):
    """
        计算 boxes_0 和 boxes_1 之间的交并比 iou

        参数：
            boxes_0:          <3 axis np.array>
                                shape [batch_size, 2, dimensions]，各个维度的意义为：
                                    batch_size： 有多少个 box
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
            boxes_1:          <3 axis np.array>
                                shape 与 boxes_0 相同。
                                特别地，当 boxes_0 与 boxes_1 中某个的 batch_size 大于 1 时，另外一个可以将 batch_size 设为 1，
                                    此时将进行自动扩增。
            return_details: <boolean> 是否以详细信息的形式返回结果
                                默认为 False，此时返回：
                                    iou <np.array>
                                        shape [batch_size]
                                当设置为 True，将返回一个 dict：
                                    details = dict(
                                        iou=<np.array>,
                                        intersection=dict(areas=<np.array>, boxes=<np.array>,),  # areas 表示面积
                                        union=dict(areas=<np.array>),
                                        boxes_0=dict(areas=<np.array>, boxes=<np.array>,),
                                        boxes_1=dict(areas=<np.array>, boxes=<np.array>,),
                                    )
    """
    # 默认参数
    paras = {
        # 必要参数
        "boxes_0": None,
        "boxes_1": None,
        "return_details": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    for key in ("boxes_0", "boxes_1"):
        paras[key] = np.asarray(paras[key])
        assert paras[key].ndim == 3 and paras[key].shape[1] == 2
    assert paras["boxes_0"].shape[-1] == paras["boxes_1"].shape[-1]
    boxes_0, boxes_1 = paras["boxes_0"], paras["boxes_1"]
    boxes_0.sort(axis=1)
    boxes_1.sort(axis=1)

    # intersection
    beg = np.maximum(boxes_0[:, 0], boxes_1[:, 0])
    end = np.minimum(boxes_0[:, 1], boxes_1[:, 1])
    edge_lens = np.maximum(end - beg, 0)
    intersection = edge_lens.prod(axis=-1)

    # union
    areas_0 = (boxes_0[:, 1] - boxes_0[:, 0]).prod(axis=-1)
    areas_1 = (boxes_1[:, 1] - boxes_1[:, 0]).prod(axis=-1)
    union = areas_0 + areas_1
    union -= intersection

    # iou
    iou = intersection / np.maximum(union, 1e-10)

    if paras["return_details"]:
        details = dict(
            iou=iou,
            intersection=dict(areas=intersection, boxes=np.concatenate([beg[:, None, ...], end[:, None, ...]], axis=1)),
            union=dict(areas=union),
            boxes_0=dict(areas=areas_0, boxes=boxes_0),
            boxes_1=dict(areas=areas_1, boxes=boxes_1),
        )
        return details
    else:
        return iou
