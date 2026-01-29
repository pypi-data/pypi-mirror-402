# from: E:\Temporary_work_area\yolo\code\numerical_characteristics
import numpy as np


def ensure_minmax(bbox):
    """
        输入一个角点形式定义的bbox，转换为 x_1,y_1 是 min，x_2,y_2 是 max 的形式
    """
    x_min, x_max = np.minimum(bbox[..., 0], bbox[..., 2]), np.maximum(bbox[..., 0], bbox[..., 2])
    y_min, y_max = np.minimum(bbox[..., 1], bbox[..., 3]), np.maximum(bbox[..., 1], bbox[..., 3])
    return [x_min, y_min, x_max, y_max]


def trans_minmax_to_xywh(bbox):
    x = (bbox[..., 0] + bbox[..., 2]) / 2
    y = (bbox[..., 1] + bbox[..., 3]) / 2
    w = np.abs(bbox[..., 0] - bbox[..., 2])
    h = np.abs(bbox[..., 1] - bbox[..., 3])
    return [x, y, w, h]


def trans_xywh_to_minmax(bbox):
    x_min = bbox[..., 0] - bbox[..., 2] / 2
    x_max = x_min + bbox[..., 2]
    y_min = bbox[..., 1] - bbox[..., 3] / 2
    y_max = y_min + bbox[..., 3]
    return [x_min, y_min, x_max, y_max]


def cal_IOU(bbox_1, bbox_2, **kwargs):
    """
        选取输入的 bbox_1, bbox_2 中的最后4维来计算 iou
        参数：
            可以通过该mode_1和mode_2参数来指定输入的 bbox_1, bbox_2 是采用哪种形式
            目前支持两种形式：
                角点形式："minmax"
                中心点加长宽的形式："xywh"
    """
    # 参数
    mode_1 = kwargs.get("mode_1", "minmax")
    mode_2 = kwargs.get("mode_2", "minmax")
    assert mode_1 in ("minmax", "xywh")  # 两种模式
    assert mode_2 in ("minmax", "xywh")
    # pre
    # 如果是 xywh 模式，先转换为 minmax 的形式
    x_11, y_11, x_12, y_12 = trans_xywh_to_minmax(bbox_1) if mode_1 == "xywh" else ensure_minmax(bbox_1)
    x_21, y_21, x_22, y_22 = trans_xywh_to_minmax(bbox_2) if mode_2 == "xywh" else ensure_minmax(bbox_2)

    # intersection
    x_1, y_1 = np.maximum(x_11, x_21), np.maximum(y_11, y_21)
    x_2, y_2 = np.minimum(x_12, x_22), np.minimum(y_12, y_22)

    width = x_2 - x_1
    height = y_2 - y_1

    # no intersection when width <= 0 or height <= 0
    width = np.where(width < 0, 0, width)
    height = np.where(height < 0, 0, height)
    intersection = width * height

    # union
    union = (x_12 - x_11) * (y_12 - y_11) + (x_22 - x_21) * (y_22 - y_21)
    union -= intersection

    # iou
    iou = intersection / union

    return iou


if __name__ == '__main__':
    b1, b2 = np.random.rand(4, 5, 6, 10), np.random.rand(4, 5, 6, 10)
    print(cal_IOU(b1, b2).shape)

    b1, b2 = np.array([1, 1, 3, 3]), np.array([2, 4, 4, 2])  # 答案是 1/7
    print(cal_IOU(b1, b2))

    b1, b2 = np.array([1, 1, 3, 3]), np.array([3, 3, 2, 2])  # 答案是 1/7
    mode_2 = "xywh"
    print(cal_IOU(b1, b2, mode_2=mode_2))

    b1, b2 = np.array([1, 1, 3, 3]), np.array([3, 3, 9, 8])  # 答案是 0
    print(cal_IOU(b1, b2))

    b1, b2 = np.array([384, 36, 402, 55]), np.array([385, 49, 402, 65])
    mode_2 = "minmax"
    print(cal_IOU(b1, b2, mode_2=mode_2))
    # 0.19921875
