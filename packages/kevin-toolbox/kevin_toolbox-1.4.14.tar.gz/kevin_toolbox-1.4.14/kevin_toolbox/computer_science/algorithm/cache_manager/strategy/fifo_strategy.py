from collections import OrderedDict
from kevin_toolbox.computer_science.algorithm.cache_manager.strategy import LRU_Strategy
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_STRATEGY_REGISTRY


@CACHE_STRATEGY_REGISTRY.register()
class FIFO_Strategy(LRU_Strategy):
    """
        删除最后一次访问时间最久远的部分
        drop items with smaller initial_time
    """

    name = ":by_initial_time:FIFO_Strategy"

    def notified_by_read_of_cache(self, key, value, metadata):
        pass


# 添加其他别名
for name in [":by_initial_time:FIFO", ":by_initial_time:First_In_First_Out", ":by_initial_time:drop_smaller"]:
    CACHE_STRATEGY_REGISTRY.add(obj=FIFO_Strategy, name=name, b_force=False, b_execute_now=False)
