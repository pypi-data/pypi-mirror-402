import heapq
from kevin_toolbox.computer_science.algorithm.cache_manager.strategy import Strategy_Base, LFU_Strategy
from kevin_toolbox.computer_science.algorithm.cache_manager.strategy.lfu_strategy import Score_to_Key
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_STRATEGY_REGISTRY


@CACHE_STRATEGY_REGISTRY.register()
class LST_Strategy(LFU_Strategy):
    """
        删除访问频率最低的部分
        drop items with smaller survival_time
    """

    name = ":by_survival_time:LST_Strategy"

    def notified_by_write_of_cache(self, key, value, metadata):
        self.record_s[key] = Score_to_Key(score=metadata["survival_time"], key=key)
        heapq.heappush(self.order_ls, self.record_s[key])

    def notified_by_read_of_cache(self, key, value, metadata):
        self.record_s[key].score = metadata["survival_time"]


# 添加其他别名
for name in [":by_survival_time:LST", ":by_survival_time:Least_Survival_Time", ":by_survival_time:drop_smaller"]:
    CACHE_STRATEGY_REGISTRY.add(obj=LST_Strategy, name=name, b_force=False, b_execute_now=False)
