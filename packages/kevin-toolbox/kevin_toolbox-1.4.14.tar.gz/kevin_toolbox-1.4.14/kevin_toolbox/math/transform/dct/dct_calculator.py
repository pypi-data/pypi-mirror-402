import torch
import numpy as np
from kevin_toolbox.math.transform import dct
from kevin_toolbox.math import utils


class DCT_Calculator:
    """
        多维dct变换
            对张量的最后几个维度进行dct变换或者逆变换

        使用方法：
            calculator = dct.Calculator(...)  # 可预设使用的转换矩阵
            outputs = calculator(inputs, reverse, ...)
        更多请参考 calculator.cal() 函数的介绍

        ps：
            - 本模块计算DCT时并没有使用类似FFT的动态规划方式来节省计算量，因为本模块更多地关注使用gpu并行计算的场景，而
                诸如文章 https://jz.docin.com/p-699413364.html 中的快速DCT都难以实行并行计算。
                因而对于 basis_series_num 较小（能够被gpu一次性装下并计算）的情况，快速DCT的实际速度较慢。
                以后有可能会针对cpu的场景，增加快速DCT的计算方式。
            - 本模块支持 torch.tensor/np.array 类型的输入，并且会将输入变量所在的设备来作为计算设备。
                因此如果需要使用 gpu 进行计算，请首先保证输入变量已经指定到某个 gpu 设备上了。
    """

    def __init__(self, **kwargs):
        """
            参数：
                sampling_points_num_ls:     <list of integers> 对应维度上，进行转换时，采样点数量，的列表
                basis_series_num_ls:        <list of integers> 对应维度上，进行转换时，使用的基函数数量，的列表
                        以上参数均可在 cal() 时再具体指定，即使提前设定也不会提前生成相关转换矩阵
        """
        # 默认参数
        paras = {
            "sampling_points_num_ls": None,
            "basis_series_num_ls": None,
        }
        # 获取参数
        paras.update(kwargs)

        # 校验参数
        for k in ["sampling_points_num_ls", "basis_series_num_ls"]:
            assert paras[k] is None or isinstance(paras[k], (list, tuple,))

        self.paras = paras

        # 变量
        self.trans_matrix_repos = dict()  # {device: {sampling_points_num/r_num: trans_matrix, ...}, ...}

    def cal(self, **kwargs):
        """
            多维dct变换
                对张量的最后几个维度进行dct变换或者逆变换

            参数：
                x:                          <torch.tensor/np.array> 输入张量
                reverse:                    <boolean> 是否进行逆变换
                sampling_points_num_ls:     <list of integers> 对应维度上，进行转换时，采样点数量，的列表
                                                不设置时，默认使用初始化时设置的值，
                                                如果进一步连初始化时也没有设置时，将尝试根据 x 和 basis_series_num_ls 推断得到
                basis_series_num_ls:        <list of integers> 对应维度上，进行转换时，使用的基函数数量，的列表
                                                不设置时，默认使用初始化时设置的值，
                                                如果进一步连初始化时也没有设置时，将尝试根据 x 和 sampling_points_num_ls 推断得到

            例子：
                在 reverse=False 正向模式下时，当输入为 x [b, n0, n1, n2] 时，
                    在设置 sampling_points_num_ls=[n0, n1, n2] 和 basis_series_num_ls=[m0, m1, m2] 下，
                    将对输入的最后 len(basis_series_num_ls)=3 个维度进行变换，得到 y [b, m0, m1, m2]

            注意：
                - 基函数的数量 basis_series_num 不应超过采样点的数量 sampling_points_num
                - 当基函数的数量 basis_series_num 小于采样点的数量 sampling_points_num 时，此时转换过程是有损的，将丢失高频信息
                - 本函数将输入变量 x 所在的设备来作为计算设备。因此如果需要使用 gpu 进行计算，请首先保证输入变量已经指定到某个 gpu 设备上了。

            建议：
                - 对于 np.array 类型的输入和 dtype!=torch.float32 的 torch.tensor 类型的输入，
                    本函数会先转换成 <torch.tensor with dtype=float32> 再进行计算，
                    因此直接使用 <torch.tensor with dtype=float32> 类型输入可以跳过该转换过程，从而实现加速。

            返回：
                y：          <torch.tensor with dtype=float32> （所在设备与输入变量保持一致）
        """
        # 默认参数
        paras = {
            # 必要参数
            "x": None,
            #
            "reverse": False,
            "sampling_points_num_ls": self.paras["sampling_points_num_ls"],
            "basis_series_num_ls": self.paras["basis_series_num_ls"],
        }
        # 获取参数
        paras.update(kwargs)

        # 校验参数
        if not torch.is_tensor(paras["x"]):
            device = torch.device("cpu")
            x = torch.tensor(paras["x"], dtype=torch.float32, device=device)
        else:
            device = paras["x"].device
            x = paras["x"].to(dtype=torch.float32)
        #
        k0, k1 = ["sampling_points_num_ls", "basis_series_num_ls"] if paras["reverse"] else ["basis_series_num_ls",
                                                                                             "sampling_points_num_ls"]
        # 正向时，参数 basis_series_num_ls 是必要的
        # 反向时，参数 sampling_points_num_ls 是必要的
        assert paras[k0] is not None, \
            f"missing required parameter {k0}"
        # 正向时，sampling_points_num_ls 应该与 x 最后几个维度保持一致
        # 反向时，basis_series_num_ls 应该与 x 最后几个维度保持一致
        if paras[k1] is not None:
            assert list(paras[k1]) == list(x.shape[-len(paras[k1]):])
        else:
            paras[k1] = list(x.shape[-len(paras[k0]):])
        #
        for k in [k0, k1]:
            assert (np.array(paras[k]) > 0).all()
        assert len(paras[k0]) == len(paras[k1]) > 0
        # basis_series_num 不应超过采样点的数量 sampling_points_num
        assert (np.array(paras["sampling_points_num_ls"]) - np.array(paras["basis_series_num_ls"]) >= 0).all(), \
            f"basis_series_num should not exceed the number of sampling points sampling_points_num"
        if device not in self.trans_matrix_repos:
            self.trans_matrix_repos[device] = dict()

        "计算"
        for i, (r_num, c_num) in enumerate(
                zip(reversed(paras["sampling_points_num_ls"]), reversed(paras["basis_series_num_ls"]))):
            # 获取转换矩阵
            if r_num not in self.trans_matrix_repos[device]:
                # 新增到库
                self.trans_matrix_repos[device][r_num] = torch.tensor(dct.generate_trans_matrix(shape=[r_num, r_num]),
                                                                      dtype=torch.float32, device=device)
            B = self.trans_matrix_repos[device][r_num][..., :c_num]
            # 将待处理维度放到最后
            x = x.transpose(-1 - i, -1)
            # 变换
            if not paras["reverse"]:
                x = x @ B
            else:
                x = x @ B.t()
        # 还原维度顺序
        new_axis_idx = list(range(x.ndim))
        new_axis_idx.insert(-len(paras["sampling_points_num_ls"]), new_axis_idx[-1])
        new_axis_idx.pop(-1)
        y = x.permute(*new_axis_idx)

        return y

    def __call__(self, x, **kwargs):
        kwargs["x"] = x
        return self.cal(**kwargs)


if __name__ == '__main__':
    a = torch.ones([100, 200, 3, 4, 5], dtype=torch.float32)
    calculator = dct.Calculator()
    b = calculator(a, reverse=False, basis_series_num_ls=[3, 2, 4])
    a1 = calculator(b, reverse=True, sampling_points_num_ls=[3, 4, 5])
    print(b.shape)
    print(a1.shape)

    from line_profiler import LineProfiler

    lp = LineProfiler()
    lp_wrapper = lp(calculator.cal)
    lp_wrapper(x=a, reverse=False, basis_series_num_ls=[3, 2, 4])
    lp.print_stats()
