from collections import defaultdict
import numpy as np
from kevin_toolbox.computer_science.algorithm.cache_manager.cache import Cache_Base
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_BUILDER_REGISTRY


def is_numeric(v):
    return v in [int, float] or (isinstance(v, type) and issubclass(v, (np.number, int, float)))


@CACHE_BUILDER_REGISTRY.register()
class Array_Cache(Cache_Base):
    """
        基于内存array的缓存结构
            它主要用于存储 Key 为非负整数（如索引 ID）的结构化数据。

        核心特性：
            - 分块存储 (Block-based Storage)：
                将数据空间划分为固定大小的块（Block）。Key 通过 key // block_size 定位块索引，
                通过 key % block_size 定位块内偏移。这种设计支持动态扩容，无需预先分配所有内存。
            - 结构化 Schema 定义：
                支持通过 value_names 和 value_types 定义类似于数据库表的列结构。
                底层使用多个并行的 NumPy 数组存储不同字段，保证了存取的高效性。
            - 稀疏性支持：
                通过 has_s 维护数据的存在性掩码（Mask），支持稀疏写入。
            - 自动内存回收：
                可选开启 b_drop_empty_block，当一个块内的所有数据都被移除时，自动释放该块占用的内存。
    """
    name = ":in_memory:Array_Cache"

    def __init__(self, **kwargs):
        """
            参数：
                block_size:             <int> 块大小
                                            决定了每个内存块能容纳的数据条目数量。
                                            - 较大的值减少了块管理的开销，但可能增加内存碎片的浪费（若数据稀疏）。
                                            - 较小的值更加灵活，但增加了字典查找的开销。
                value_names:            <list of str> 数据字段名称列表（Schema 定义）。
                value_types:            <list of str> 数据字段对应的类型列表。
                                            必须与 value_names 等长。支持字符串形式（如 'int', 'np.float32'）或直接传入类型对象。
                                            初始化块时，将使用这些类型创建对应的 NumPy 数组。
                b_drop_empty_block:     <boolean> 是否自动丢弃空块
                                            默认 False，当设置为 True 时，每当通过 _remove_freely 移除数据导致某一个块变为空（所有位置 has=False）时，
                                            自动从内存中删除该块以释放资源。
        """
        # 默认参数
        paras = {
            "block_size": 1000000,
            "value_names": None,
            "value_types": None,
            "b_drop_empty_block": False
        }

        # 获取参数
        paras.update(kwargs)
        # 校验参数
        for k in ["value_names", "value_types"]:
            assert isinstance(paras[k], (list, tuple)) and len(paras[k]) > 0, \
                f'{k} must be a non-empty list of str'
        assert len(paras["value_names"]) == len(paras["value_types"]), \
            "value_names and value_types must have the same length"
        self.paras = paras
        self.value_types = []
        for i in paras["value_types"]:
            try:
                temp = eval(i)
            except:
                temp = i
            self.value_types.append(temp)
        self.cache_s = dict()  # {<block idx>: {<value_name>: [<value_type>, ....], ...}, ....}
        self.has_s = dict()  # {<block idx>: [<boolean>, ....], ....}
        self.count_s = defaultdict(int)  # {<block idx>: <int>, ....}

    def __check_key(self, key):
        if not (isinstance(key, int) and key >= 0):
            raise KeyError(f"key must be a non-negative integer")
        block_idx = key // self.paras["block_size"]
        module_idx = key % self.paras["block_size"]
        return block_idx, module_idx

    def _read_freely(self, key):
        block_idx, module_idx = self.__check_key(key=key)
        return {k: self.cache_s[block_idx][k][module_idx] for k in self.paras["value_names"]}

    def _write_freely(self, key, value):
        block_idx, module_idx = self.__check_key(key=key)
        assert isinstance(value, dict)
        #
        if block_idx not in self.has_s:
            self.has_s[block_idx] = np.zeros(shape=self.paras["block_size"], dtype=bool)
        if not self.has_s[block_idx][module_idx]:
            self.count_s[block_idx] += 1
            self.has_s[block_idx][module_idx] = True
        #
        if block_idx not in self.cache_s:
            self.cache_s[block_idx] = {
                k: (np.zeros(shape=self.paras["block_size"], dtype=v_) if is_numeric(v_) else np.empty(
                    shape=self.paras["block_size"], dtype=v_)) for
                k, v_ in zip(self.paras["value_names"], self.value_types)}
        for k, v in value.items():
            self.cache_s[block_idx][k][module_idx] = v

    def _remove_freely(self, key):
        block_idx, module_idx = self.__check_key(key=key)
        self.has_s[block_idx][module_idx] = False
        for k, v_ in zip(self.paras["value_names"], self.value_types):
            self.cache_s[block_idx][k][module_idx] = 0 if is_numeric(v_) else None
        self.count_s[block_idx] -= 1
        if self.paras["b_drop_empty_block"] and self.count_s[block_idx] <= 0:
            temp = self.cache_s.pop(block_idx)
            temp2 = self.has_s.pop(block_idx)
            del temp, temp2

    def has(self, key):
        block_idx, module_idx = self.__check_key(key=key)
        if block_idx in self.has_s:
            return self.has_s[block_idx][module_idx]
        return False

    def len(self):
        return sum(self.count_s.values())

    @property
    def occupation(self):
        return len(self.has_s) * self.paras["block_size"]

    def clear(self):
        self.cache_s.clear()
        self.has_s.clear()
        self.count_s.clear()

    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.cache_s.update(state_dict["cache_s"])
        self.has_s.update(state_dict["has_s"])
        self.count_s.update(state_dict["count_s"])

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"cache_s": self.cache_s, "has_s": self.has_s, "count_s": self.count_s}
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp


# 添加其他别名
for name in [":in_memory:Array", ":in_memory:AC"]:
    CACHE_BUILDER_REGISTRY.add(obj=Array_Cache, name=name, b_force=False, b_execute_now=False)
