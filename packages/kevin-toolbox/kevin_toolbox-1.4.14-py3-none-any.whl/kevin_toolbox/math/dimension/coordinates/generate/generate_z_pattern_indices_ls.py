import numpy as np


def generate_z_pattern_indices_ls(**kwargs):
    """
        生成 从原点出发进行之字形（Z形）遍历 的下标列表
            本质上就是从原点出发，按照汉明距离（各axis的坐标之和）在 shape 对应的长方体内进行宽度优先遍历
            生成的坐标列表是 indices_ls 格式，index_ls 的具体定义参见 coordinates.convert()

        原理：
            约定：
                - 使用记号 (n,k) 表示仅考虑 shape 里面前n个axis（亦即仅对前n个axis的取值进行排列组合）时，汉明距离为k的下标列表
                - 使用记号 x | (n,k) 表示在上面所述的下标列表中的所有下标的前面加上值 x
            则有递推式：
                (n+1,k) := 0|(n,k) + 1|(n,k-1) + 2|(n,k-2) + ...
            我们以 shape=[3, 3, 2, ...] 为例演示这一过程：
                首先对于 axis=0
                    (0,0)   (0,1)   (0,2)   (0,3)
                    0       1       2       None  # 超出axis=0的取值范围
                然后根据 axis=0 的结果递推 axis=1 的情况：
                    (1,0) := 0|(0,0)
                    00
                            (1,1) := 0|(0,1) + 1|(0,0)
                            01  # 0|(0,1)
                            10  # 1|(0,0)
                                    (1,2) := 0|(0,2) + 1|(0,1) + 2|(0,0)
                                    02
                                    11
                                    20
                                           (1,3) := 0|(0,3) + 1|(0,2) + 2|(0,1) + 3|(0,0)
                                            # 0|(0,3) 不存在，忽略
                                            12
                                            21
                                            # 3|(0,0) 3超出取值范围，后面抛弃
                                                    (1,4) := 0|(0,4) + 1|(0,3) + 2|(0,2) + 3|(0,1) + 4|(0,0)
                                                    # 0|(0,4) 不存在，忽略
                                                    # 1|(0,3) 不存在，忽略
                                                    22
                                                    # 3|(0,1) 3超出取值范围，后面抛弃
                依次类推：
                    (2,0)   (2,1)   (2,2)   (2,3)   (2,4)   (2,5)
                    000     001     002     012     022     122
                            010     011     021     112
                            100     020     102     121
                                    101     111
                                    110     120

        参数：
            shape：              <list/tuple of integers>

        返回：
            indices_ls：         <nparray of nparray> 坐标列表。
    """
    # 默认参数
    paras = {
        # 必要参数
        "shape": None,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    assert isinstance(paras["shape"], (list, tuple,)) and len(paras["shape"]) > 0

    dim_size_ls = [(dim, size) for dim, size in enumerate(paras["shape"])]
    dim_size_ls.sort(key=lambda x: x[-1])
    res = [None for _ in range(sum(paras["shape"]))]
    #
    for dim, size in dim_size_ls:
        if res[0] is None:  # init
            for i in range(size):
                res[i] = np.zeros(shape=[1, len(paras["shape"])])
                res[i][0, dim] = i
        else:  # 迭代
            for np1_k in reversed(range(sum(paras["shape"]))):
                indices = []
                # 组合公式： (n+1,k) := 0|(n,k) + 1|(n,k-1) + 2|(n,k-2) + ...
                for head, n_kp1 in enumerate(reversed(range(np1_k + 1))):
                    if head >= size:
                        break
                    if res[n_kp1] is None:
                        continue

                    res[n_kp1][:, dim] = head
                    indices.append(res[n_kp1])
                if len(indices) == 0:
                    continue
                indices = np.concatenate(indices, axis=0)
                res[np1_k] = indices
    # 整合
    res = [i for i in res if i is not None]
    res = np.concatenate(res, axis=0)
    assert len(res) == np.prod(paras["shape"])

    return res


# if __name__ == '__main__':
#     shape = [3, 3]
#     indices_ls = generate_z_pattern_indices_ls(shape=shape)
#     print(indices_ls)
