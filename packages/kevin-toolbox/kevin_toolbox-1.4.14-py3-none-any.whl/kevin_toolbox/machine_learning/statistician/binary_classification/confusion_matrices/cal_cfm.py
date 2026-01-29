import torch
from kevin_toolbox.patches.for_torch.math import my_around
from kevin_toolbox.patches.for_torch.compatible import where as torch_where
from .convert import convert_to_numpy

# 计算设备（尽量使用gpu来加速计算）
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')


def cal_cfm(scores, labels, to_numpy=True, decimals_of_scores=None, **kwargs):
    """
        将 scores 中所有不同的取值作为模型的 threshold，然后统计出在不同 threshold 下模型的预测结果中，
        TP、FN、FP、TN的数量。

        统计 TP、FN、FP、TN 的原理：
            首先依据 scores 从大到小对 labels 和 scores 进行排序，
            对于给定的一个阈值 threshold，我们选取 scores >= threshold 的部分对应的 labels，
            假设前 m 个满足阈值，
            则 labels[:m] 的部分会被模型判断为 positive，在这一部分的样本中
                label 为 0 是假阳性 FP 样本，
                label 为 1 是真阳性 TP 样本，
            则剩余的 labels[m:] 的部分会被模型判断为 negative，在这一部分的样本中
                label 为 0 是真阴性 TN 样本，
                label 为 1 是假阴性 FN 样本。

        参数：
            scores:             list of floats indicating the confidence of the model to predict the sample
                                as a positive sample.
                                表示模型将样本预测为正样本的置信度
                                    shape [sample_nums, 1]
            labels:             list of 0/1 describing the true label of the sample
                                描述样本的真实标签，其中1表示正样本，0表示负样本。
                                    shape [sample_nums, 1]
            to_numpy（可选）:     boolean，是否将结果从 tensor 转换为numpy
                                    默认为True
            decimals_of_scores（可选）：     integer，scores 要保留的小数位数（直接截取而非四舍五入）
                                    实际上，scores的取值有非常多，
                                    为了避免 thresholds 过多，可以通过限制 scores 的小数位，来对结果进行进一步合并和去重，
                                    从而减少内存占用。
                                    默认为 None，表示不对 scores 进行操作。
        返回：
            confusion_matrices： 描述了不同 threshold 取值下，二分类混淆矩阵中的各项 TP、FN、FP、TN 的取值，
                                是包含以下字段的一个 dict：
                                    thresholds：         scores 中不同的取值，从大到小排列
                                    tp_ls：              在对应的 threshold 取值下，有多少个样本是 true positive
                                    tn_ls：              true negative
                                    fp_ls：              false positive
                                    fn_ls：              false negative
                                    （以上的 shape 都是 [diff_nums]，其中 diff_nums 表示 scores 中有多少个不同的元素）
    """
    assert len(labels.shape) == len(scores.shape) == 2 and labels.shape[-1] == scores.shape[-1] == 1 and labels.shape[
        0] == scores.shape[0], \
        Exception(f"Error: The shapes of scores ({scores.shape}) and labels ({labels.shape}) are not equal, "
                  f"or do not satisfy the form of [sample_nums, 1]")

    scores_ = torch.tensor(scores, device=device, dtype=torch.float32) if not isinstance(scores,
                                                                                         torch.Tensor) else scores
    labels_ = torch.tensor(labels, device=device, dtype=torch.float32) if not isinstance(labels,
                                                                                         torch.Tensor) else labels
    if decimals_of_scores is not None:
        scores_ = my_around(scores_, decimals=decimals_of_scores, inplace=scores_ is not scores, floor=True)

    # 按照 scores 从大到小进行排序
    sorted_scores, sorted_indices = torch.sort(scores_, descending=True, dim=0)
    sorted_labels = labels_[sorted_indices.reshape(-1)]

    # 统计取前 m 个预测为正时，模型的预测结果
    # 其中 tp_ls[m] 表示前 m 个样本中，都多少个是label为真的。
    tp_ls = torch.cumsum(sorted_labels, dim=0, dtype=torch.int64)
    fp_ls = torch.cumsum(sorted_labels == 0, dim=0, dtype=torch.int64)

    # 找出 scores 不同的取值下的结果
    diff_scores = sorted_scores.clone()
    diff_scores[:-1] -= sorted_scores[1:]  # 取梯度
    diff_scores[-1, 0] = -1  # 保证最后一个元素被下面的 torch.where 取出
    diff_indices = torch_where(diff_scores != 0)
    #
    tp_ls = tp_ls[diff_indices]
    fp_ls = fp_ls[diff_indices]

    res = dict(thresholds=sorted_scores[diff_indices],
               tp_ls=tp_ls, fp_ls=fp_ls,
               tn_ls=fp_ls[-1] - fp_ls, fn_ls=tp_ls[-1] - tp_ls)

    if to_numpy:
        res = convert_to_numpy(res, decimals_of_scores)

    return res
