from kevin_toolbox.computer_science.algorithm.cache_manager.cache import Cache_Base
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_BUILDER_REGISTRY


@CACHE_BUILDER_REGISTRY.register()
class Memo_Cache(Cache_Base):
    """
        基于内存dict的缓存结构
    """
    name = ":in_memory:Memo_Cache"

    def __init__(self, **kwargs):
        self.cache_s = dict()

    def _read_freely(self, key):
        return self.cache_s[key]

    def _write_freely(self, key, value):
        self.cache_s[key] = value

    def _remove_freely(self, key):
        self.cache_s.pop(key)

    def has(self, key):
        return key in self.cache_s

    def len(self):
        return len(self.cache_s)

    def clear(self):
        self.cache_s.clear()

    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.cache_s.update(state_dict["cache_s"])

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"cache_s": self.cache_s}
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp


# 添加其他别名
for name in [":in_memory:Memo", ":in_memory:MC", ":in_memory:memory"]:
    CACHE_BUILDER_REGISTRY.add(obj=Memo_Cache, name=name, b_force=False, b_execute_now=False)
