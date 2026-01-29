"""
本模块是实现数据集分块生成的核心模块，依赖于执行器 Executor 模块
"""
from .by_samples import get_executor_ls_by_samples as by_samples
from .by_block import get_executor_ls_by_block as by_block
