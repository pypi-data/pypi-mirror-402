from kevin_toolbox.computer_science.data_structure import Executor
from .along_axis import get_executor_ls_by_block_along_axis
from .along_diagonal import get_executor_ls_by_block_along_diagonal


def get_executor_ls_by_block_of_triangle(factory, chunk_step, need_to_generate, include_diagonal=True, **kwargs):
    """
        通过调用 verification.Factory 中的 generate_by_block() 函数，
            来对矩阵的上三角部分，
            生成一系列的执行器 executor_ls，
            每个执行器在被 executor() 调用后都将返回一个数据集
        参数：
            factory:                verification.Factory 实例
            chunk_step:             每个分块的大小
            need_to_generate:       需要生成的字段
                                        （参见 Factory.generate_by_block() 中的介绍）
            include_diagonal:       是否包含对角线
    """

    width = len(factory.paras["features"])  # 矩阵的宽度
    assert width > 0, \
        Exception("Error: the length of features in the input factory should be larger than 0!")

    if include_diagonal:
        offset = 0
    else:
        # 如果要除去对角线，相当于去掉矩阵的第0列和最后一行
        # 宽度减1
        width -= 1
        # 在迭代时还需要为坐标添加一个偏置
        offset = 1

    # block的数量
    chunk_nums = (width - 1) // chunk_step + 1

    """
    执行器
    """
    executor_ls, size_ls = [], []

    # 对于完整的 block（去除对角上、和最后一列上的block）
    #     将整个block作为一个dataset
    #     dataset_size = chunk_step * chunk_step
    for i in range(chunk_nums - 1):
        i_0 = i * chunk_step
        i_1 = i_0 + chunk_step
        for j in range(i + 1, chunk_nums - 1):
            j_0 = j * chunk_step + offset
            j_1 = j_0 + chunk_step
            # 计算
            paras = dict(i_0=i_0, i_1=i_1, j_0=j_0, j_1=j_1,
                         pick_triangle=False, need_to_generate=need_to_generate)
            executor_ls.append(Executor(func=factory.generate_by_block,
                                        kwargs=paras))
            size_ls.append(factory.cal_size_of_block(**paras))

    # 对于对角线上的半个 block
    #     将两个上三角拼凑为一个dataset
    #     dataset_size = chunk_step * (chunk_step + 1)
    # 注意：
    #     当上三角的数量是奇数或者最后一个三角是残缺的话，
    #     该部分将与接下来的最后一列的部分头部组成一个dataset
    executor_ls_temp, size_ls_temp = get_executor_ls_by_block_along_diagonal(factory,
                                                                             i_0=0,
                                                                             i_1=width,
                                                                             j_0=offset,
                                                                             j_1=width + offset,
                                                                             chunk_step=chunk_step,
                                                                             need_to_generate=need_to_generate,
                                                                             pick_triangle=True, include_diagonal=True)
    executor_ls.extend(executor_ls_temp)
    size_ls.extend(size_ls_temp)

    # 对于最后一列
    #     第一个矩形将与前面残缺的上三角整合为一个dataset，该矩形的行数将根据缺少部分的数量计算得到，从而保证
    #     chunk_step * chunk_step <= dataset_size <= chunk_step * (chunk_step + 1)
    #     接下来的矩形将调整行数以尽量贴近上界，
    #     对于完整的矩形有
    #     chunk_step * chunk_step < dataset_size <= chunk_step * (chunk_step + 1)
    #     对于最后一个可能残缺的矩阵，有
    #     dataset_size <= chunk_step * (chunk_step + 1)
    # 这里承接上面的  res
    if chunk_nums > 1:
        executor_ls_temp, size_ls_temp = get_executor_ls_by_block_along_axis(factory,
                                                                             i_0=0,
                                                                             i_1=(chunk_nums - 1) * chunk_step,
                                                                             j_0=(chunk_nums - 1) * chunk_step + offset,
                                                                             j_1=width + offset,
                                                                             axis_to_split="i",
                                                                             size_upper=chunk_step * (chunk_step + 1),
                                                                             need_to_generate=need_to_generate,
                                                                             pre_executor=executor_ls.pop(-1),
                                                                             pre_size=size_ls.pop(-1))
        executor_ls.extend(executor_ls_temp)
        size_ls.extend(size_ls_temp)

    # 综合而言，
    #     除最后一个dataset以外，都有
    #     chunk_step * chunk_step <= dataset_size <= chunk_step * (chunk_step + 1)
    #     最后一个dataset可能是残缺的，有
    #     0 < dataset_size <= chunk_step * (chunk_step + 1)
    return executor_ls, size_ls
