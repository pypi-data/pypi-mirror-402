from kevin_toolbox.data_flow.core.reader import UReader, Unified_Reader_Base
from .cal_cfm import cal_cfm
from .merge_cfm_ls import merge_cfm_ls
from .convert import convert_to_numpy


def cal_cfm_iteratively_by_chunk(scores, labels, chunk_step=None, to_numpy=True, decimals_of_scores=None, **kwargs):
    """
        迭代地从 scores, labels 和取出一部分来通过 cal_cfm() 分别计算出 confusion_matrices，
        然后再使用 merge_cfm_ls() 对结果进行合并。
            避免直接对全部进行计算造成对内存占用过大。

        参数（详细介绍参见 cal_cfm()）：
            scores:             表示模型将样本预测为正样本的置信度
            labels:             描述样本的真实标签，其中1表示正样本，0表示负样本。
                注意： scores 和 labels 支持变量的形式，和使用 Unified_Reader_Base 包裹的形式

        可选参数：
            chunk_step:         integer，每个分块的大小
                                    默认为 None，表示将所有输入视为一个分块，此时该函数退化为 cal_cfm()
            to_numpy:           boolean，是否将结果从tensor转换为numpy
                                    默认为 True
            decimals_of_scores：     integer，scores 要保留的小数位数（直接截取而非四舍五入）
                                    默认为 None，表示不对 scores 进行操作。
                                    实际上，scores的取值有非常多，
                                    为了避免 thresholds 过多，可以通过限制 scores 的小数位，来对结果进行进一步合并和去重，
                                    从而减少内存占用。

        返回（详细介绍参见 cal_cfm()）：
            confusion_matrices： 描述了不同 threshold 取值下，二分类混淆矩阵中的各项 TP、FN、FP、TN 的取值
    """
    scores = scores if isinstance(scores, (Unified_Reader_Base,)) else UReader(var=scores)
    labels = labels if isinstance(labels, (Unified_Reader_Base,)) else UReader(var=labels)
    assert isinstance(scores, (Unified_Reader_Base,)) and isinstance(labels, (Unified_Reader_Base,)), \
        Exception(f"Error: scores and labels need to be wrapped with Unified_Reader_Base!")
    assert len(scores) == len(labels) > 0
    chunk_step = len(scores) if chunk_step is None else chunk_step
    assert isinstance(chunk_step, (int,)) and 0 < chunk_step <= len(scores), \
        Exception(f"Error: chunk_step({chunk_step}) should be between 1 and len(scores)({len(scores)}),"
                  f" or use the default value of None!")

    chunk_nums = (len(scores) - 1) // chunk_step + 1
    cfm_ls = []
    for i in range(chunk_nums):
        beg = i * chunk_step
        end = beg + chunk_step
        cfm = cal_cfm(scores.read(beg, end), labels.read(beg, end),
                      to_numpy=False, decimals_of_scores=decimals_of_scores)
        cfm_ls.append(cfm)
        if len(cfm_ls) >= 3:  # 计算多少个就合并一次
            cfm_ls = [merge_cfm_ls(cfm_ls, to_numpy=False)]

    if len(cfm_ls) > 1:
        cfm = merge_cfm_ls(cfm_ls, to_numpy=False)
    else:
        cfm = cfm_ls[0]

    if to_numpy:
        cfm = convert_to_numpy(cfm, decimals_of_scores)

    return cfm
