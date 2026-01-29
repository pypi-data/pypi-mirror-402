from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.machine_learning.dataset.face.verification.merge import merge


def get_executor_ls_by_block_along_diagonal(factory, i_0, i_1, j_0, j_1, chunk_step, need_to_generate,
                                            pick_triangle=True, include_diagonal=True):
    """
        通过调用 verification.Factory 中的 generate_by_block() 函数，
            来在（i_0, i_1, j_0, j_1）指定的子矩阵范围内，
            沿着 对角线，以 chunk_step 为间隔生成一系列的执行器 executor_ls，
            每个执行器在被 executor() 调用后都将返回一个数据集
        参数：
            factory:                verification.Factory 实例
            i_0, i_1, j_0, j_1:     子矩阵的范围
                                        （支持多种方式输入，具体参见 Factory.generate_by_block() 中的介绍）
            chunk_step:             chunk的长宽
            pre_res:                前置的数据集
                                        第一个chunk产生的数据集将与pre_res整合为一个dataset并返回
            need_to_generate:       需要生成的字段
                                        （参见 Factory.generate_by_block() 中的介绍）
            pick_triangle:          只取block的上三角
            include_diagonal:       是否包含对角线

        关于返回的数据集大小：
            当 pick_triangle=True 时，
            只取上三角
                将每两个 chunk 矩形的上三角，将两个上三角拼凑为一个dataset，有
                    dataset_size = chunk_step * (chunk_step + offset)
                    其中，当包含对角线上元素时，offset=1，不包含则为-1。
                当上三角的数量是奇数或者最后一个三角是残缺的话，
                    对于最后一个残缺的数据集，有
                    dataset_size <= chunk_step * (chunk_step + offset)
            当 pick_triangle=False 时，
            取整个block
                此时对于完整的矩形，有
                    dataset_size = chunk_step * chunk_step
                对于最后一个残缺的矩形，有
                    dataset_size <= chunk_step * chunk_step
    """
    i_len = i_1 - i_0 if isinstance(i_0, (int,)) else len(i_0)
    j_len = j_1 - j_0 if isinstance(j_0, (int,)) else len(j_0)
    assert 0 < i_len == j_len

    executor_ls, size_ls = [], []
    #
    count = 0
    while count < i_len:
        # 范围
        step = min(i_len - count, chunk_step)

        # 计算
        paras = dict(i_0=i_0 + count, i_1=i_0 + count + step,
                     j_0=j_0 + count, j_1=j_0 + count + step,
                     pick_triangle=pick_triangle,
                     include_diagonal=include_diagonal,
                     need_to_generate=need_to_generate)
        executor_ls.append(Executor(func=factory.generate_by_block,
                                    kwargs=paras))
        size_ls.append(factory.cal_size_of_block(**paras))
        #
        count += step

    # 合并
    for k in range(len(executor_ls) // 2):
        # 数据集
        u, v = executor_ls.pop(k), executor_ls.pop(k)
        executor_ls.insert(k, Executor(func=merge, f_args=[u, v]))
        # size
        u, v = size_ls.pop(k), size_ls.pop(k)
        size_ls.insert(k, u + v)

    return executor_ls, size_ls
