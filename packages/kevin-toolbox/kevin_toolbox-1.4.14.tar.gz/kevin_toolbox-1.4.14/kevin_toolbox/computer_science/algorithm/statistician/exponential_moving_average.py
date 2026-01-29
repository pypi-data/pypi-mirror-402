from kevin_toolbox.computer_science.algorithm.statistician import Accumulator_Base


class Exponential_Moving_Average(Accumulator_Base):
    """
        滑动平均器
            支持为每个输入数据配置不同的权重
    """

    def __init__(self, **kwargs):
        """
            参数：
                keep_ratio:             <float> 对历史值的保留比例。
                                            其意义为： 大致等于计算过去 1/keep_ratio 个数据的平均值
                                            默认为 0.99
                                            当设置为 0 时相当于仅保留最新的数据
                bias_correction:        <boolean> 是否开启偏差修正。
                                            默认为 True
                update_func:            <function> 用于融合新旧数据的函数。
                                            默认为：
                                            lambda w_old, v_old, w_new, v_new: w_old * v_old + w_new * v_new
                                            你可以利用该接口，指定你需要的融合方式，比如融合后对数据进行归一化：
                                            lambda w_old, v_old, w_new, v_new: normalize(w_old * v_old + w_new * v_new)
                指定输入数据的格式，有三种方式：
                    1. 显式指定数据的形状和所在设备等。
                        data_format:        <dict of paras>
                                其中需要包含以下参数：
                                    type_:              <str>
                                                            "numpy":        np.ndarray
                                                            "torch":        torch.tensor
                                    shape:              <list of integers>
                                    device:             <torch.device>
                                    dtype:              <torch.dtype>
                    2. 根据输入的数据，来推断出形状、设备等。
                        like:               <torch.tensor / np.ndarray / int / float>
                    3. 均不指定 data_format 和 like，此时将等到第一次调用 add()/add_sequence() 时再根据输入来自动推断。
                    以上三种方式，默认选用最后一种。
                    如果三种方式同时被指定，则优先级与对应方式在上面的排名相同。
        """

        # 默认参数
        paras = {
            # 超参数
            "keep_ratio": 0.99,
            "bias_correction": True,
            # 指定累加方式
            "update_func": lambda w_old, v_old, w_new, v_new: w_old * v_old + w_new * v_new,
            # 指定输入数据的形状、设备
            "data_format": None,
            "like": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(paras["keep_ratio"], (int, float,)) and 0 <= paras["keep_ratio"] <= 1
        #
        super().__init__(**paras)

    def add_sequence(self, var_ls, **kwargs):
        for var in var_ls:
            self.add(var, **kwargs)

    def add(self, var, weight=1, **kwargs):
        """
            添加单个数据

            参数:
                var:                数据
                weight:             <int/float> 权重。
                                        默认为 1
        """
        if self.var is None:
            self.var = self._init_var(like=var)
        new_ratio = (1 - self.paras["keep_ratio"]) * weight
        keep_ratio = (1 - new_ratio)
        # 累积
        self.var = self.paras["update_func"](keep_ratio, self.var, new_ratio, var)
        #
        self.state["total_nums"] += 1
        self.state["bias_fix"] *= keep_ratio

    def get(self, bias_correction=None, **kwargs):
        """
            获取当前累加值
                当未初始化时，返回 None

            参数:
                bias_correction:        <boolean> 是否开启偏差修正。
                                            默认使用初始化时设定的值
        """
        if self.var is None:  # 未初始化
            return None
        bias_correction = self.paras["bias_correction"] if bias_correction is None else bias_correction
        if bias_correction:
            return self.var / (1 - self.state["bias_fix"] + 1e-10)
        else:
            return self.var

    @staticmethod
    def _init_state():
        return dict(
            total_nums=0,
            bias_fix=1,
        )


if __name__ == '__main__':
    import torch
    import numpy as np

    seq = list(torch.tensor(range(1, 10)))
    wls = np.asarray([0.1] * 5 + [0.9] + [0.1] * 4) * 0.1
    ema = Exponential_Moving_Average(keep_ratio=0.9, bias_correction=True)
    for i, (v, w) in enumerate(zip(seq, wls)):
        ema.add(var=v, weight=w)
        print(i, v, ema.get(), ema.state["bias_fix"])
