import numpy as np


def generate_dct_trans_matrix(**kwargs):
    """
        生成用于进行1维离散余弦变换（DCT）的变换基

        使用方法：
            假设要变换的1维信号队列为 X [k, n]
                其中：
                - n 为信号序列的长度（在DCT中一般将输入的信号序列视为经过时轴对称延拓后得到的周期为2n的序列）
                - k 为信号的通道数。
                你可以将 X 视为 k 个长度为 n 的1维信号的组合。
            使用该函数生成一个转换基 B [n, m]
                其中：
                - m 表示基向量/基函数的数量（数量越大越能整合高频信号）
                - n 为基向量的长度/基函数的离散采样点数量，与输入周期信号的周期的一半相等
            则变换过程为 Y = X @ B
                得到的 Y [k, m]

        如何推广到多维？
            原理：
                由于频域变换的维度可分离性，因此可以将多维 DCT 变换分解为对信号的每个维度单独做1维 DCT 变换。
            具体方法：
                以 2d DCT 变换为例，假设输入信号为 X [k, n0, n1]
                    1.0 首先使用该函数生成针对于维度 n1 的变换基 B1 [n1, m1]
                    1.1 对维度 n1 进行变换：Z = X @ B1，得到 Z [k, n0, m1]
                    1.2 对 Z 进行转置 Z = Z.permute(0, 2, 1) 得到 Z [k, m1, n0]
                    2.0 类似地生成变换基  B0 [n0, m0]
                    2.1 对维度 n0 进行变换：Y = Z @ B0，得到 Y [k, m1, m0]
                    2.2 对 Y 进行转置恢复维度顺序 Y = Y.permute(0, 2, 1) 得到 Z [k, m0, m1]
        参数：
            sampling_points_num:    <integer> 转换矩阵的行数，对应 基函数的离散采样点数量
                                                与输入周期信号的周期的一半相等
            basis_series_num:       <integer> 转换矩阵的列数，对应 基向量/基函数的数量
                                                数量越大越能整合高频信号，但不应超过采样点的数量 sampling_points_num
                                                如果超过则会导致列向量不再两两正交，也不一定保证单位化
            shape:                  <list of integers> 长度为 2 的列表，记录了 [sampling_points_num, basis_series_num]
                当 sampling_points_num ... 和 shape 被同时设定时，以前者为准。

        返回：
            B       <np.array> shape [r_num, c_num]
                矩阵中各元素为
                    B[r,c] := g(c) * sqrt(2/r_num) * cos( (2*r + 1) * c * pi / (2*r_num) )
                        其中 g(c) := sqrt(1/2) if c==0 else 1

        技巧：
            当两个转换矩阵的 r_num 相同时，小矩阵可以直接从大矩阵中截取，而不需要重新计算。
    """
    # 默认参数
    paras = {
        # 必要参数
        "sampling_points_num": None,
        "basis_series_num": None,
        # 别名
        "shape": None,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    for i, k in enumerate(["sampling_points_num", "basis_series_num"]):
        if paras[k] is None:
            assert isinstance(paras["shape"], (list, tuple,)) and len(paras["shape"]) == 2
            paras[k] = paras["shape"][i]
        assert isinstance(paras[k], (int,)) and paras[k] > 0
    r_num, c_num = paras["sampling_points_num"], paras["basis_series_num"]
    if c_num > r_num:
        print(f"Warning: basis_series_num {c_num} should not be larger than sampling_points_num {r_num}!")

    B = np.zeros(shape=(r_num, c_num))
    # cos
    for r in range(r_num):
        for c in range(c_num):
            B[r, c] = np.cos((2 * r + 1) * c * np.pi / (2 * r_num))

    # g(c) * sqrt(2/r_num)
    g = np.ones(shape=(1, c_num)) * np.sqrt(2 / r_num)
    g[..., 0] = g[..., 0] * np.sqrt(1 / 2)
    B = B * g

    return B


if __name__ == '__main__':
    print(generate_dct_trans_matrix(shape=[4, 4]))
    print(generate_dct_trans_matrix(shape=[6, 4]))
    print(generate_dct_trans_matrix(shape=[4, 6]))
    print(np.sum(generate_dct_trans_matrix(shape=[1, 2]) ** 2, axis=0))
