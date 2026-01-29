import numpy as np
from .computational_tree import Node


def concat_crops_into_whole(**kwargs):
    """
        将 crop 按照对应的 box 指示的位置，以行优先的内存顺序，进行拼接、展平

        工作流程：
            首先根据 box_ls 构建 computational_tree，然后将 crop 按照对应的 box 分配到计算图中对应的叶节点，调用计算图中的 concat()
            进行合并，最后从计算图的根节点中取出最后合并得到的结果。

        参数：
            crop_ls:        <list of np.array/tensor>
            box_ls:         <list of np.arrays>
                                each element is an array with shape [2, dimensions]
                                各个维度的意义为：
                                    2：          box 的两个轴对称点
                                    dimensions： 坐标的维度
                                要求：
                                    - 各个 box 应该是已经 sorted 的，亦即小坐标在前大坐标在后。
                                        例如 box=[[1,2],[0,4]] 是错误的。
                                        而 box=[[0,2],[1,4]] 是合法的。
                                    - 各个 box 在坐标轴上的投影之间没有重叠部分
                                    函数 geometry.for_boxes.boolean_algebra() 返回的 boxes 结果，以及
                                    函数 geometry.for_boxes.detect_collision() 返回的 node_ls 中每个 node 下面
                                    的 node.description["by_boxes"] 都符合该要求。
            beg_axis:       <integer> 上面提供的 box 中指定的坐标是从 crop 的第几个 axis 开始对应的。
                                例如： beg_axis=1 时，box=[[i,j],[m,n]] 表示该 crop 是从原张量的 [:, i:m, j:n, ...] 部分截取出来的。
            computational_tree: <Node> 计算图
                                默认为 None，函数将根据输入的 box_ls 自动构建计算图。
                                你也可以将已有的计算图代入该参数中，以跳过构建计算图的步骤，节省计算量。
            return_details: <boolean> 是否以详细信息的形式返回结果
                                默认为 False，此时返回：
                                    whole:  <np.array/tensor> 对 crop_ls 进行合并后的结果
                                当设置为 True，将返回一个 dict：
                                    details = dict(
                                        whole = <np.array/tensor>,  # 对 crop_ls 进行合并后的结果
                                        box_ls = <list of np.arrays>,  # 按照 内存顺序 对 box_ls 进行排序后的结果
                                        crop_ls = <list of np.array/tensor>,  # 按照 内存顺序 对 crop_ls 进行排序后的结果
                                        beg_axis = beg_axis,  # 对应与输入的 beg_axis
                                        computational_tree = <Node>,  # 计算图
                                    )
        返回：
            whole 或者 details
    """
    # 默认参数
    paras = {
        # 必要参数
        "crop_ls": None,
        "box_ls": None,
        #
        "beg_axis": 0,
        "computational_tree": None,
        "return_details": False,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert isinstance(paras["crop_ls"], (list,)) and len(paras["crop_ls"]) > 0
    crop_ls = paras["crop_ls"]
    #
    assert isinstance(paras["box_ls"], (list,)) and len(paras["box_ls"]) == len(crop_ls)
    assert paras["box_ls"][0].ndim == 2 and paras["box_ls"][0].shape[1] == 2
    box_ls = paras["box_ls"]
    #
    assert isinstance(paras["beg_axis"], (int,))
    beg_axis = paras["beg_axis"]
    end_axis = beg_axis + box_ls[0].shape[-1] - 1
    assert 0 <= beg_axis <= end_axis < crop_ls[0].ndim
    # 构建计算图
    if paras["computational_tree"] is None:
        tree = Node(box_ls=box_ls)
        tree.build_tree()
        tree.init_tree()
    else:
        tree = paras["computational_tree"]
    assert isinstance(tree, (Node,))

    # 按行优先进行多级排序
    sorted_node_ls = sorted(tree.get_leaf_nodes(), key=lambda x: x.details["box_ls"][0][0].tolist())
    temp = sorted(zip(box_ls, crop_ls), key=lambda x: x[0][0].tolist())
    sorted_crop_ls = [crop for _, crop in temp]
    sorted_box_ls = [box for box, _ in temp]

    for node, crop in zip(sorted_node_ls, sorted_crop_ls):
        node.var = crop

    tree.concat(beg_axis=beg_axis)
    whole = tree.var

    if paras["return_details"]:
        details = dict(
            whole=whole,
            crop_ls=sorted_crop_ls,
            box_ls=sorted_box_ls,
            beg_axis=beg_axis,
            computational_tree=tree,
        )
        return details
    else:
        return whole
