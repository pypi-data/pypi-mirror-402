import os
import optuna
from kevin_toolbox.data_flow.file import json_
from kevin_toolbox.patches.for_optuna import build_sampler, build_storage


def build_study(output_dir=None, feasible_domain_path=None, **kwargs):
    """
        参数：
            storage:            <dict/str> 数据库链接
                                    有两种指定方式：
                                        1. <str> 直接使用给定的 URI 链接
                                        2. <dict> 使用 build_storage() 根据参数键值对构建数据库
                                    建议使用第2种方式，更具通用性，并且在 mysql 模式下支持新建数据库。
            sampler:            <dict> 采样优化算法
                                    将使用 build_sampler() 进行构建

            output_dir:         <path> 用于补充 build_storage() 中的 output_dir 参数
            feasible_domain_path:   <path> 用于补充 build_sampler() 中的 feasible_domain 参数
            （其他参数参见 optuna.create_study() 函数介绍）
    """
    # 处理参数
    #   storage
    if "storage" in kwargs:
        if isinstance(kwargs["storage"], (str,)) and kwargs["storage"].startswith("mysql:"):
            temp_ls = list(kwargs["storage"].split(":", 1))
            temp_ls[0] = "mysql+pymysql"
            kwargs["storage"] = ":".join(temp_ls)
        elif isinstance(kwargs["storage"], (dict,)):
            kwargs["storage"] = build_storage(output_dir=output_dir, **kwargs["storage"]).url
    #   sampler
    if "sampler" in kwargs and isinstance(kwargs["sampler"], (dict,)):
        if feasible_domain_path is not None:
            kwargs["sampler"]["feasible_domain"] = json_.read(file_path=feasible_domain_path,
                                                              b_use_suggested_converter=True)
        kwargs["sampler"] = build_sampler(**kwargs["sampler"])
    user_attr_s = kwargs.pop("user_attr_s", dict())

    # 创建实验
    study = optuna.create_study(**kwargs)
    for k, v in user_attr_s.items():
        study.set_user_attr(k, v)
    if "storage" not in user_attr_s and "storage" in kwargs:
        study.set_user_attr("storage", kwargs["storage"])

    return study
