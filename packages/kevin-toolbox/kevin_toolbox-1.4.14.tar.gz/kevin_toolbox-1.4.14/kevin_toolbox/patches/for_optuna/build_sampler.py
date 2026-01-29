import optuna


def build_sampler(name, seed=None, feasible_domain: dict = None, **kwargs):
    """
        构建超参数采样器实例

        参数：
            name：               <str> 算法的种类
                                    目前支持：
                                        - optuna.samplers 下的算法。
                                            比如要使用 TPE 算法，可以输入 "optuna.samplers.TPESampler"，或者直接简写成 "TPESampler"
            seed:               <int> 随机种子
                                    建议：对于多进程优化，不同进程所用的随机种子也应该不同，以产生不同的参数配置
            feasible_domain:    <dict> 对于 GridSampler 算法，可以通过指定该参数来生成算法所需的 search_space 参数。
            **kwargs:           其余参数将用于初始化算法实例
    """
    # 参数校验
    if not name.startswith("optuna"):
        name = "optuna.samplers." + name
    #
    if seed is not None:
        kwargs["seed"] = seed
    #
    if name.endswith("GridSampler"):
        # 需要补充 search_space 参数
        assert isinstance(feasible_domain, (dict,)), \
            f'for sampler {name}, feasible_domain(<dict>) must be specified to generate search_space'
        search_space = dict()
        for k, v in feasible_domain.items():
            assert v["p_type"] in ["categorical"], \
                f'for sampler {name}, feasible_domain(<dict>) should be categorical, but {k} is {v["p_type"]}'
            search_space[k] = v["choices"]
        #
        kwargs["search_space"] = search_space
    cls = eval(name)
    return cls(**kwargs)
