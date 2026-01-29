def cal_tpr_and_fpr(cfm):
    """
        根据混淆矩阵来计算出各个 threshold 下的 tpr、fpr

        计算 tpr、fpr 的原理：
            tpr = TP/TP+FN  # 正样本中被模型检出的比例，越大越好
            fpr = FP/FP+TN  # 负样本中被模型误检的比例，越小越好

        背景知识：
            假设前 m 个满足阈值，则有 TP+FP == m，且 TP、FP 都是单调递增的，
            因此，fpr 和 tpr 都是随着m增加而递增的，
            我们希望在两者之间取一个平衡点，亦即 threshold。
            一般是对于给定 fpr 时，求出此时的 tpr和 threshold，
            记为 tpr=xxx@fpr=xxx 和 threshold=xxx@fpr=xxx
    """
    cfm["tpr_ls"] = cfm["tp_ls"] / (cfm["tp_ls"] + cfm["fn_ls"] + 1e-14)
    cfm["fpr_ls"] = cfm["fp_ls"] / (cfm["fp_ls"] + cfm["tn_ls"] + 1e-14)
    return cfm
