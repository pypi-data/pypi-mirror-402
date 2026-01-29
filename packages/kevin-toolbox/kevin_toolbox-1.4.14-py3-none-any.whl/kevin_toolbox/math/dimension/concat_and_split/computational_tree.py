import numpy as np
from kevin_toolbox.math import utils


class Node:
    """
        计算图节点
            使用该节点类实例构建的计算图，将支持把节点中的张量 var 按照对应的 box 指示的位置（var在源张量中的位置），
            以行优先的内存顺序，进行拼接、展平和其逆向的分割。

        节点包含以下属性：
            sub_nodes:          <dict of node> 记录子节点。
                                        定义了计算图中节点之间的连接关系。
            var:                <np.array/torch.tensor> 节点值。
                                        用于保存节点上的计算结果。
            details:            <dict of paras> 节点属性。
                                        用于保存节点内的处理函数的参数，定义了节点的行为。
                                        包含以下参数：
                                            box_ls:     表示节点中的 var 是根据这些 box 从源张量中截取出来并拼接而成的。
                                                        each element is an array with shape [2, dimensions]
                                                        各个维度的意义为：
                                                            2：          box 的两个轴对称点
                                                            dimensions： 坐标的维度
                                            axis:       表示节点将根据 box_ls 中第 axis 个轴对 box_ls 和 var 进行分割，然后将分割结果
                                                            分别传递给对应的子节点。
                                            slice:      本节点的 var 和 box_ls 是如何从父节点中分割得到的。
                                            shape:      本节点中 var 的目标形状。
                （看到这里一脸懵逼很正常，不要担心，下面将结合具体的工作流程来介绍节点中各个属性的具体作用）

        使用方法：
            本节介绍如何使用本节点类，构建一个树状的计算图，并进行推理计算。

            1. 构建计算图：
                root_node = Node(box_ls=...)
                root_node.build_tree()  # 将从根节点出发，根据 box_ls 构建计算图

                假设输入的 box_ls = [ [[0, 0],
                                     [4, 4]],
                                    [[0, 4],
                                     [4, 16]],
                                    [[4, 0],
                                     [16, 4]],
                                    [[4, 4],
                                     [16, 16]] ] 则具体的构建过程为：
                首先从根节点出发：

                          root_node

                    box_ls=[box_0,1,2,3]
                    slice(None,None)
                    aixs=0

                其中 axis=0 表示我们先看 box 中的第0个轴（对应上面的第一列），可以看到该轴有两个分段，分别是 slice(0,4) 和 slice(4,16)。
                根据分段构建第一层子节点，将属于 slice(0,4) 的两个 box 分给 sub_node_0，依次类推：

                          root_node  ───────┬──────── sub_node_0
                                            │
                    box_ls=[box_0,1,2,3]    │      box_ls=[box_0,1]
                    slice(None,None)        │      slice(0,4)
                    aixs=0                  │
                                            │
                                            │
                                            │
                                            │
                                            │
                                            └──────── sub_node_1

                                                   box_ls=[box_2,3]
                                                   slice(4,16)

                对于第一层子节点，axis=1，看第1个轴，依次类推，构建第二层节点：
                                                                      ┌────── leaf_node_0
                                                                      │
                          root_node  ───────┬──────── sub_node_0 ─────┤    box_ls=[box_0]
                                            │                         │    slice(0,4)
                    box_ls=[box_0,1,2,3]    │      box_ls=[box_0,1]   │    axis=2
                    slice(None,None)        │      slice(0,4)         │
                    aixs=0                  │      axis=1             └────── leaf_node_1
                                            │
                                            │                              box_ls=[box_1]
                                            │                              slice(4,16)
                                            │                              axis=2
                                            │
                                            └──────── sub_node_1 ─────┬────── leaf_node_2
                                                                      │
                                                   box_ls=[box_2,3]   │    box_ls=[box_2]
                                                   slice(4,16)        │    slice(0,4)
                                                   axis=1             │    axis=2
                                                                      │
                                                                      └────── leaf_node_3

                                                                           box_ls=[box_3]
                                                                           slice(4,16)
                                                                           axis=2

                当 axis==box.shape[-1] 时，到达叶节点，停止构建。此时叶节点中应该有且只有一个 box。

            2. 检查并初始化计算图：
                root_node.init_tree()  # 从叶节点出发，检查各个节点的合法性，并初始化相关的变量，依次向上直至根节点。

                检查叶节点中 box 数量为1，并计算 box 的 size，依次向上累加：

                                                                      ┌────── leaf_node_0
                                                                      │
                          root_node  ◄──────┬──────── sub_node_0 ◄────┤    box_ls=[box_0]
                                            │                         │    slice(0,4)
                    box_ls=[box_0,1,2,3]    │      box_ls=[box_0,1]   │    axis=2
                    slice(None,None)        │      slice(0,4)         │    size=4*4=16
                    aixs=0                  │      axis=1             └────── leaf_node_1
                    size=64+192=256         │      size=16+48=64
                                            │                              box_ls=[box_1]
                                            │                              slice(4,16)
                                            │                              axis=2
                                            │                              size=4*12=48
                                            └──────── sub_node_1 ◄────┬────── leaf_node_2
                                                                      │
                                                   box_ls=[box_2,3]   │    box_ls=[box_2]
                                                   slice(4,16)        │    slice(0,4)
                                                   axis=1             │    axis=2
                                                   size=48+144=192    │    size=12*4=48
                                                                      └────── leaf_node_3

                                                                           box_ls=[box_3]
                                                                           slice(4,16)
                                                                           axis=2
                                                                           size=12*12=144

            3. 使用计算图进行推理：
                本计算图支持两种计算

                split(beg_axis)  # 从根节点出发，根据节点属性 details 中的参数，对节点值 var 进行分割，然后将分割的片段分别传递给后继的子节点中的 var。
                                依次向下迭代，直至叶节点。
                                最后分割的结果保存在叶节点的 var 中，可以通过 get_leaf_nodes() 获取子节点并读取其值。

                以上面的计算图为例，下面展示一次典型的 split() 计算过程：
                假设根节点中 var.shape=[10,256,3]，从源张量的第1个轴开始分割，亦即 beg_axis=1。

                首先，根节点读取其子节点的 size，根据 root_node->size / sub_node->size 的比例，确定 root_node.var 在 beg_axis + aixs 对应的维度上的分割比例。
                然后进行分割。

                          root_node  ───────┬───────► sub_node_0
                    var:[10,256,3]          │      var=root_node.var[10,:64,3]
                    box_ls=[box_0,1,2,3]    │      box_ls=[box_0,1]
                    slice(None,None)        │      slice(0,4)
                    aixs=0                  │      axis=1
                    size=256                │      size=64
                                            │
                                            │
                                            │
                                            │
                                            └───────► sub_node_1
                                                   var=root_node.var[10,64:256,3]
                                                   box_ls=[box_2,3]
                                                   slice(4,16)
                                                   axis=1
                                                   size=192

                再将子节点的 var 的第 beg_axis + aixs 个维度，reshape 成 [length of sub_node.slice,-1] 。
                （如果最后的 -1 维度计算结果为 1，则将该维度去除）

                          root_node  ───────┬───────► sub_node_0
                    var:[10,256,3]          │      var:[10,4,16,3]
                    box_ls=[box_0,1,2,3]    │      box_ls=[box_0,1]
                    slice(None,None)        │      slice(0,4)
                    aixs=0                  │      axis=1
                    size=256                │      size=64
                                            │
                                            │
                                            │
                                            │
                                            └───────► sub_node_1
                                                   var:[10,12,16,3]
                                                   box_ls=[box_2,3]
                                                   slice(4,16)
                                                   axis=1
                                                   size=192

                依次类推，得到：

                                                                      ┌─────► leaf_node_0
                                                                      │    var:[10,4,4,3]
                          root_node  ───────┬───────► sub_node_0 ─────┤    box_ls=[box_0]
                    var:[10,256,3]          │      var:[10,4,16,3]    │    slice(0,4)
                    box_ls=[box_0,1,2,3]    │      box_ls=[box_0,1]   │    axis=2
                    slice(None,None)        │      slice(0,4)         │
                    aixs=0                  │      axis=1             └─────► leaf_node_1
                                            │                              var:[10,4,12,3]
                                            │                              box_ls=[box_1]
                                            │                              slice(4,16)
                                            │                              axis=2
                                            │
                                            └───────► sub_node_1 ─────┬─────► leaf_node_2
                                                   var:[10,12,16,3]   │    var:[10,12,4,3]
                                                   box_ls=[box_2,3]   │    box_ls=[box_2]
                                                   slice(4,16)        │    slice(0,4)
                                                   axis=1             │    axis=2
                                                                      │
                                                                      └─────► leaf_node_3
                                                                           var:[10,12,12,3]
                                                                           box_ls=[box_3]
                                                                           slice(4,16)
                                                                           axis=2



                concat(beg_axis)  # 从叶节点出发，将叶节点中的 var 向上传递给父节点。父节点根据 details 对从子节点中获取的 var_ls 进行合并，
                                    保存到本节点的 var 中，然后继续将本节点的 var 传递给更上层的节点。依次向上迭代，直至根节点。
                                    最后总的合并结果保存在根节点的 var 中。

                split 和 concat 互为逆操作。

                本类还提供了针对 split 和 concat 操作的进一步封装：
                    10
                    20
                这两个函数相较于原始的 split() 等函数提供了更完善的接口检查，建议使用这两个函数。
    """

    def __init__(self, **kwargs):
        """
            设定关键参数

            参数：
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
                    （为节省计算量，本函数不对 box_ls 的合法性进行完整的检查。）
        """

        # 默认参数
        paras = {
            # 必要参数
            "box_ls": [],
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(paras["box_ls"], (list,))
        if len(paras["box_ls"]) > 0:
            assert paras["box_ls"][0].ndim == 2 and paras["box_ls"][0].shape[1] == 2

        self.sub_nodes = dict()  # {<node>.slice[0]: <node>, ...}  分割起始点到子节点的映射
        self.var = None
        self.details = dict(
            #
            box_ls=paras["box_ls"],
            # 潜变量（根据 box_ls 推断得到，不需要外部设定）
            axis=0,  # 本节点根据该轴进行分割。本节点的子节点（若有）将根据该轴的下一个轴进行分割，因此本参数随着树的深度增加而增加，该参数也暗含了树的深度信息。
            slice=[None, None],
            size=None,
        )

    def build_tree(self):
        """
            构建计算图
        """
        assert len(self.details["box_ls"]) > 0, \
            f'Error: box_ls of node with depth {self.details["axis"]} is empty! ' \
            f'please invoke `node.details["box_ls"]=box_ls` before build_tree!'

        # 到达叶节点。（递归出口）
        if self.details["axis"] >= self.details["box_ls"][0].shape[-1]:
            return

        # 添加子节点。
        for box in self.details["box_ls"]:
            new_slice = box[:, self.details["axis"]].tolist()
            if new_slice[0] not in self.sub_nodes:
                node = Node()
                node.details["slice"] = new_slice
                node.details["axis"] = self.details["axis"] + 1
                self.sub_nodes[new_slice[0]] = node
            node = self.sub_nodes[new_slice[0]]
            assert new_slice == node.details["slice"], \
                f'{new_slice} == {node.details["slice"]} ？\n' \
                f'Error: Please check whether the projection of the input box_ls on each coordinate axis overlaps'
            node.details["box_ls"].append(box)

        for node in self.sub_nodes.values():
            node.build_tree()

    def init_tree(self):
        """
            检查并初始化计算图
        """
        # 先初始化子节点
        for node in self.sub_nodes.values():
            node.init_tree()

        # 定义每个节点的初始化行为
        if len(self.sub_nodes) == 0:
            # 叶节点
            #   检查叶节点的合法性
            assert len(self.details["box_ls"]) == 1
            #   根据 box 计算 size
            box = self.details["box_ls"][0]
            self.details["size"] = np.prod(box[1] - box[0])
        else:
            # 非叶节点
            #   累加子节点的 size
            self.details["size"] = sum([node.details["size"] for node in self.sub_nodes.values()])

    def print_tree(self):
        """
            依照DFS打印树
        """
        tap = "\t" * 2 * self.details["axis"]
        print(f'{tap}depth:{self.details["axis"]} {self.details}')
        print(f'{tap}------------ divided by axis {self.details["axis"]} ------------')
        for node in self.sub_nodes.values():
            node.print_tree()

    def clear_tree(self, depths):
        """
            清理节点的 var

            参数:
                depths:     <list/tuple/set of integers>  要清除哪些深度的层
        """
        assert isinstance(depths, (list, tuple, set,))

        depths = set(depths)
        if self.details["axis"] in depths:
            depths.remove(self.details["axis"])
            self.var = None

        if len(depths) > 0:
            for node in self.sub_nodes.values():
                node.clear_tree(depths)

    def get_leaf_nodes(self):
        """
            以列表形式返回所有叶节点
        """
        leaf_nodes = []
        if len(self.sub_nodes) == 0:
            leaf_nodes.append(self)
        else:
            for node in self.sub_nodes.values():
                leaf_nodes.extend(node.get_leaf_nodes())
        return leaf_nodes

    def split(self, beg_axis=0):
        """
            按照 BFS 的顺序，逐层向下分割节点中的 var

            参数：
                beg_axis:       <integer> 从 var 的第几个轴开始分割。
        """
        assert isinstance(beg_axis, (int,))
        assert self.details["size"] is not None, \
            f"Error: computational graph not initialized! please invoke init_tree() before inference!"
        assert self.var is not None, \
            f'before splitting node with depth {self.details["axis"]}, its var needs to be assigned a value'

        axis = beg_axis + self.details["axis"]
        slices = [slice(None, None)] * (axis + 1)
        beg = 0
        for _, node in sorted(self.sub_nodes.items(), key=lambda x: x[0]):
            # 截取出属于各个子节点的部分 var
            if node.details["size"] * self.details["size"] == 0:
                end = beg
            else:
                end = beg + int(round(node.details["size"] / self.details["size"] * self.var.shape[axis]))
            slices[axis] = slice(beg, end)
            #
            sub_var = self.var[tuple(slices)]
            # 对截取的部分按照子节点的要求进行 reshape
            sub_shape = list(self.var.shape)
            sub_span = node.details["slice"][1] - node.details["slice"][0]
            sub_shape[axis] = sub_span
            if len(node.sub_nodes) > 0:
                # 对于非叶节点，需要再增加一个维度留给其子节点进行分割
                if sub_span > 0:  # 考虑 sub_span=0 的情况
                    assert node.details["size"] % sub_span == 0
                    sub_shape.insert(axis + 1, node.details["size"] // sub_span)
                else:
                    sub_shape.insert(axis + 1, 0)
            #
            node.var = sub_var.reshape(sub_shape)
            #
            beg = end

        for node in self.sub_nodes.values():
            node.split(beg_axis=beg_axis)

    def concat(self, beg_axis=0):
        """
            按照 DFS 的顺序，从叶节点逐层向上合并节点中的 var

            参数：
                beg_axis:       <integer> 叶节点中的 box 指定的坐标是从 var 的第几个 axis 开始对应的
                                例如： beg_axis=1 时，box=[[i,j],[m,n]] 表示叶节点中的 var 是从原张量的 [:, i:m, j:n, ...] 部分截取出来的。
        """

        if len(self.sub_nodes) == 0:
            # 叶节点
            box = self.details["box_ls"][0]
            assert self.var is not None \
                   and list(self.var.shape[beg_axis:beg_axis + box.shape[-1]]) == (box[1] - box[0]).tolist()
        else:
            # 非叶节点
            #   让子节点进行合并
            for node in self.sub_nodes.values():
                node.concat(beg_axis=beg_axis)
            #   再合并子节点中的 var
            var_ls = [node.var for _, node in sorted(self.sub_nodes.items(), key=lambda x: x[0])]
            end_axis = beg_axis + self.details["axis"]
            _, function_table = utils.get_function_table_for_array_and_tensor(var_ls[0])
            concat, flatten = function_table["concat"], function_table["flatten"]
            # 合并
            res = concat(var_ls, axis=end_axis)
            # 打平
            if beg_axis < end_axis:
                # 将已 concat 的部分进行展平，展平后的 ndim 将减1
                res = flatten(res, axis_0=end_axis - 1, axis_1=end_axis)
            self.var = res
