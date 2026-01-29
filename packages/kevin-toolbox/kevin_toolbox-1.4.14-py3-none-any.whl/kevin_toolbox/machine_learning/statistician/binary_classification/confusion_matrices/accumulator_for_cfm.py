from .cal_cfm_iteratively_by_chunk import cal_cfm_iteratively_by_chunk
from .merge_cfm_ls import merge_cfm_ls
from .convert import convert_to_numpy


class Accumulator_for_Confusion_Matrices:
    """
        支持多种方式计算 confusion_matrices，并进行累积。

        用法：
            1. __init__( decimals_of_scores=xxx )
                在初始化阶段设置 scores/thresholds 的统计精度
            2. __call__( scores=xx, labels=xx, chunk_step=xx )
                计算 confusion_matrices
                可以多次调用，结果将进行累积
            3. get( to_numpy=xxx )
                获取结果
            4. reset( decimals_of_scores=xxx )
                重置
    """

    def __init__(self, **kwargs):
        """
            设定关键参数
            参数：
                decimals_of_scores：     integer，scores 要保留的小数位数（直接截取而非四舍五入）
                                    默认为 None，表示不对 scores 进行操作。
                                    实际上，scores的取值有非常多，
                                    为了避免 thresholds 过多，可以通过限制 scores 的小数位，来对结果进行进一步合并和去重，
                                    从而减少内存占用。
        """
        self.paras = None
        self.cfm = None
        self.reset(**kwargs)

    def reset(self, **kwargs):
        """
            重置
        """
        # 默认参数
        paras = {
            "decimals_of_scores": None,
        }
        # 获取参数
        paras.update(kwargs)
        # 校验参数
        if paras["decimals_of_scores"] is not None:
            assert isinstance(paras["decimals_of_scores"], (int,)) and paras["decimals_of_scores"] >= 0

        self.cfm = None
        self.paras = paras

    def __call__(self, scores, labels, **kwargs):
        """
            计算 confusion_matrices
            参数（详细介绍参见 cal_cfm_iteratively_by_chunk()）：
                scores:             表示模型将样本预测为正样本的置信度
                labels:             描述样本的真实标签，其中1表示正样本，0表示负样本。
                    注意： scores 和 labels 支持变量的形式，和使用 Unified_Reader_Base 包裹的形式
                chunk_step:         integer，每个分块的大小
                                        默认为 None，表示将所有输入视为一个分块，此时该函数退化为 cal_cfm()
        """
        cfm = cal_cfm_iteratively_by_chunk(scores, labels,
                                           chunk_step=kwargs.get("chunk_step", None),
                                           decimals_of_scores=self.paras["decimals_of_scores"],
                                           to_numpy=False)
        if self.cfm is not None:
            self.cfm = merge_cfm_ls([self.cfm, cfm], to_numpy=False)
        else:
            self.cfm = cfm
        return self

    def get(self, to_numpy=True):
        """
            获取结果
        """
        cfm = convert_to_numpy(self.cfm, self.paras["decimals_of_scores"]) if to_numpy else self.cfm
        return cfm
