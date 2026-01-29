from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.data_flow.core.reader import Unified_Reader_Base
from kevin_toolbox.machine_learning.dataset.face.verification import Factory, SUPPORT_TO_GENERATE


def get_executor_ls_by_samples(factory, samples, **kwargs):
    """
        通过调用 verification.Factory 中的 generate_by_samples() 函数，
            来根据 samples 生成一系列的执行器 executor_ls，
            每个执行器在被 executor() 调用后都将返回一个数据集

        参数：
            samples:                list of feature_id pairs
                                        np.array with dtype=np.int
                                        shape [sample_nums, 2]
                                        需要被 Unified_Reader_Base 包裹
            factory:                verification.Factory 实例

        设定数据集大小：
            chunk_step:             每次返回的数据集的大小的上界（根据实际内存容量来选择）
            upper_bound_of_dataset_size：    chunk_step 参数的别名
                                        同时设置时，以两者最小值为准。

        输入到 Factory.generate_by_samples 中：
            need_to_generate:       需要生成的字段
                                        （参见 Factory.generate_by_samples() 中的介绍）
            feature_ids_is_sequential:       boolean，feature_ids 是否以1为间距递增的
                                        （参见 Factory.generate_by_samples() 中的介绍）

        返回：
            executor_ls：            list of get_executor_ls that can generate dataset by using get_executor_ls()
            size_ls：                产生的数据集的预期大小
    """
    "paras"
    paras = {
        "chunk_step": None,
        "upper_bound_of_dataset_size": None,
    }

    # 获取参数
    paras.update(kwargs)

    # 校验参数
    # samples
    assert isinstance(samples, (Unified_Reader_Base,)), \
        Exception(f"The type of input factory should be {Unified_Reader_Base}, but get a {type(samples)}!")
    # factory
    assert isinstance(factory, (Factory,)), \
        Exception(f"The type of input factory should be {Factory}, but get a {type(factory)}!")
    # chunk_step / upper_bound_of_dataset_size
    temp_ls = []
    if paras["upper_bound_of_dataset_size"] is not None:
        temp_ls.append(paras["upper_bound_of_dataset_size"])
    if paras["chunk_step"] is not None:
        temp_ls.append(paras["chunk_step"])
    assert len(temp_ls) > 0
    chunk_step = min(temp_ls)

    "body"
    executor_ls, size_ls = [], []
    # 填充参数（静态）
    kwargs__ = dict()
    for key in {"need_to_generate", "feature_ids_is_sequential"}:
        if key in kwargs:
            kwargs__[key] = kwargs[key]
    #
    count = 0
    while count < len(samples):
        # step
        step = min(chunk_step, len(samples) - count)
        # 填充参数（动态生成）
        f_kwargs = dict(samples=Executor(func=samples.read, args=[count, count + step]))
        for key in SUPPORT_TO_GENERATE:
            if key in kwargs and kwargs[key] is not None:
                f_kwargs[key] = Executor(func=kwargs[key].read, args=[count, count + step])
        # 计算
        executor_ls.append(Executor(func=factory.generate_by_samples,
                                    f_kwargs=f_kwargs, kwargs=kwargs__))
        size_ls.append(step)
        #
        count += step

    # 综合而言，
    #     除最后一个dataset以外，都有
    #     dataset_size = chunk_step
    #     最后一个dataset可能是残缺的，有
    #     0 < dataset_size <= dataset_size
    return executor_ls, size_ls
