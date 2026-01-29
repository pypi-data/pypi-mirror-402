from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.machine_learning.dataset.face.verification.merge import merge


def get_executor_ls_by_block_along_axis(factory, i_0, i_1, j_0, j_1, axis_to_split, size_upper, need_to_generate,
                                        pre_executor=None, pre_size=None):
    """
        通过调用 verification.Factory 中的 generate_by_block() 函数，
            来在（i_0, i_1, j_0, j_1）指定的子矩阵范围内，
            沿着 axis 指定的轴线方向，以 size_upper 为目标大小进行分割，
            生成一系列的执行器 executor_ls，
            每个执行器在被 executor() 调用后都将返回一个数据集
        参数：
            factory:                verification.Factory 实例
            i_0, i_1, j_0, j_1:     子矩阵的范围
                                        （支持多种方式输入，具体参见 Factory.generate_by_block() 中的介绍）
            axis_to_split:          分割子矩阵的方向
                                        可选值： ["i", "j"]
                                        以 "i" 为例，此时子矩阵沿行分割为 [i_0, i_0+step, ... ,i_1]
            size_upper:             每个分块的目标大小（大小的上界）
            pre_executor:           前置的数据集生成器
                                        第一个chunk产生的数据集将与pre_executor整合为一个dataset并返回
            pre_size:               前置数据集的大小
            need_to_generate:       需要生成的字段
                                        （参见 Factory.generate_by_block() 中的介绍）

        关于返回的数据集大小（以axis="i"为例，令j_len:=j_1-j_0）：
            当 pre_executor=None 时，
                对于前面完整的矩形，该矩形的行数将根据与size_upper相差的部分的数量计算得到，
                从而保证合并后返回的数据集尽量贴近上界，有
                dataset_size = size_upper//j_len * j_len
                对于最后一个残缺的矩形，有
                dataset_size <= size_upper
            当 pre_executor 有值时，
                第一个矩形将与 pre_executor 整合为一个dataset，有
                dataset_size <= min( size_upper//j_len * j_len, len(pre_executor) )
                其他同上。
    """
    assert axis_to_split in ["i", "j"]
    i_len = i_1 - i_0 if isinstance(i_0, (int,)) else len(i_0)
    j_len = j_1 - j_0 if isinstance(j_0, (int,)) else len(j_0)
    assert i_len > 0 and j_len > 0
    len_fix, len_to_split = (j_len, i_len) if axis_to_split == "i" else (i_len, j_len)

    executor_ls, size_ls = [], []
    #
    count = 0
    while count < len_to_split:
        # step
        if count == 0 and pre_executor is not None:
            # 对于第一个矩形
            assert isinstance(pre_size, (int,))
            step = (size_upper - pre_size) // len_fix
            if step <= 0:  # pre_executor 已经够大了，不需要再补充
                executor_ls.append(pre_executor)
                pre_executor = None
                continue
        else:
            step = size_upper // len_fix
        step = min(step, len_to_split - count)

        # 范围
        if axis_to_split == "i":
            i_0_, i_1_ = count, count + step
            if not isinstance(i_0, (int,)):
                i_0_, i_1_ = i_0[i_0_:i_1_], None
            j_0_, j_1_ = j_0, j_1
        else:
            j_0_, j_1_ = count, count + step
            if not isinstance(j_0, (int,)):
                j_0_, j_1_ = j_0[j_0_:j_1_], None
            i_0_, i_1_ = i_0, i_1

        # 计算
        paras = dict(i_0=i_0_, i_1=i_1_, j_0=j_0_, j_1=j_1_,
                     pick_triangle=False, need_to_generate=need_to_generate)
        executor_ls.append(Executor(func=factory.generate_by_block,
                                    kwargs=paras))
        size_ls.append(factory.cal_size_of_block(**paras))

        # 对于第一个矩形，进行合并
        if count == 0 and pre_executor is not None:
            # 数据集
            u, v = pre_executor, executor_ls.pop(0)
            executor_ls.insert(0, Executor(func=merge, f_args=[u, v]))
            # size
            u, v = pre_size, size_ls.pop(0)
            size_ls.insert(0, u + v)

        #
        count += step

    return executor_ls, size_ls
