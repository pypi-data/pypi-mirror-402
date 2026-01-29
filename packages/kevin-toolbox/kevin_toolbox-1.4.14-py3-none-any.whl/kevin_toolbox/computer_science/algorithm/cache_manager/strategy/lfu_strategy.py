import heapq
from kevin_toolbox.computer_science.algorithm.cache_manager.strategy import Strategy_Base
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_STRATEGY_REGISTRY


class Score_to_Key:
    def __init__(self, score, key):
        self.score = score
        self.key = key

    def __lt__(self, other):
        return self.score < other.score

    def __eq__(self, other):
        return self.score == other.score

    def __gt__(self, other):
        return self.score > other.score

    def __repr__(self):
        return f"Counts_to_Key(key:{self.key}, score:{self.score})"


@CACHE_STRATEGY_REGISTRY.register()
class LFU_Strategy(Strategy_Base):
    """
        删除访问频率最低的部分
        drop items with smaller counts
    """

    name = ":by_counts:LFU_Strategy"

    def __init__(self):
        self.order_ls = list()  # 最小堆
        self.record_s = dict()

    def notified_by_write_of_cache(self, key, value, metadata):
        assert (metadata is None or metadata["counts"] == 0) and key not in self.record_s
        self.record_s[key] = Score_to_Key(score=0, key=key)
        heapq.heappush(self.order_ls, self.record_s[key])

    def notified_by_read_of_cache(self, key, value, metadata):
        assert metadata is None or metadata["counts"] == self.record_s[key].score + 1
        self.record_s[key].score += 1

    def notified_by_remove_of_cache(self, key, metadata):
        temp = self.record_s.pop(key)
        temp.score = -1
        heapq.heapify(self.order_ls)
        temp = heapq.heappop(self.order_ls)
        assert temp.key == key

    def notified_by_clear_of_cache(self):
        self.record_s.clear()
        self.order_ls.clear()

    def suggest(self, refactor_size):
        heapq.heapify(self.order_ls)
        res = []
        temp_ls = []
        for _ in range(len(self.order_ls) - refactor_size):
            temp = heapq.heappop(self.order_ls)
            res.append(temp.key)
            temp_ls.append(temp)
        self.order_ls = temp_ls + self.order_ls
        return res

    def clear(self):
        self.notified_by_clear_of_cache()


# 添加其他别名
for name in [":by_counts:LFU", ":by_counts:Least_Frequently_Used", ":by_counts:drop_smaller"]:
    CACHE_STRATEGY_REGISTRY.add(obj=LFU_Strategy, name=name, b_force=False, b_execute_now=False)

if __name__ == "__main__":
    max_heap = []
    for i, j in [(-5, "a"), (-2, "adafd"), (-7, "ad"), (-1, "a"), (-10, "fasfde")]:
        heapq.heappush(max_heap, Score_to_Key(i, j))
    print(max_heap)
