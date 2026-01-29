import numpy as np


def cal_iou_between_box(**kwargs):
    """
        计算 box_0 和 box_1 之间的交并比 iou

        参数：
            box_0:          <np.array>
                                shape [2, dimensions]，各个维度的意义为：
                                    2：          box的两个轴对称点
                                    dimensions： 坐标的维度
            box_1:          <np.array>
                                与 box_0 类似。
            return_details: <boolean> 是否以详细信息的形式返回结果
                                默认为 False，此时返回：
                                    iou <float>
                                当设置为 True，将返回一个 dict：
                                    details = dict(
                                        iou=<float>,
                                        intersection=dict(area=<float>, box=<np.array>,),  # area 表示面积
                                        union=dict(area=<float>),
                                        box_0=dict(area=<float>, box=<np.array>,),
                                        box_1=dict(area=<float>, box=<np.array>,),
                                    )
    """
    # 默认参数
    paras = {
        # 必要参数
        "box_0": None,
        "box_1": None,
        "return_details": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    for key in ("box_0", "box_1"):
        paras[key] = np.asarray(paras[key])
        assert paras[key].ndim == 2 and paras[key].shape[0] == 2
    assert paras["box_0"].shape[1] == paras["box_1"].shape[1]
    box_0, box_1 = paras["box_0"], paras["box_1"]
    for box in (box_0, box_1):
        box.sort(axis=0)

    # intersection
    beg = np.maximum(box_0[0], box_1[0])
    end = np.minimum(box_0[1], box_1[1])
    edge_lens = np.maximum(end - beg, 0)
    intersection = edge_lens.prod()

    # union
    union = 0
    for box in (box_0, box_1):
        union += (box[1] - box[0]).prod()
    union -= intersection

    # iou
    if union > 0:
        iou = intersection / union
    else:
        iou = 0

    if paras["return_details"]:
        details = dict(
            iou=iou,
            intersection=dict(area=intersection, box=np.asarray([beg, end])),
            union=dict(area=union),
            box_0=dict(area=(box_0[1] - box_0[0]).prod(), box=box_0),
            box_1=dict(area=(box_1[1] - box_1[0]).prod(), box=box_1),
        )
        return details
    else:
        return iou
