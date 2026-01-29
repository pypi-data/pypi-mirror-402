from .cache import Cache_Base
from .variable import CACHE_BUILDER_REGISTRY


class Cache_Manager_wto_Strategy:
    """
        不绑定任何策略的缓存管理器

        提供以下接口：
            - 添加条目 add(key, value, b_allow_overwrite)
            - 获取条目 get(key, b_add_if_not_found, default_factory, default)
            - 删除并返回条目 pop(key)
            - 判断是否有该条目 has()
            - 清空所有内容 clear()
            - 加载和保存状态 load_state_dict(), state_dict()

        并支持以下用法：
            通过 len(.) 获取缓存大小，通过 in 操作符判断是否有某个条目
    """

    def __init__(self, **kwargs):
        """
            参数：
                cache:                  <str/dict/Cache_Base> 缓存种类
        """
        # 默认参数
        paras = {
            "cache": ":in_memory:Memo",
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        # cache
        assert isinstance(paras["cache"], (str, dict, Cache_Base)), \
            "cache must be a string, dict of paras or a Cache_Base object"
        if isinstance(paras["cache"], str):
            cache = CACHE_BUILDER_REGISTRY.get(name=paras["cache"])()
        elif isinstance(paras["cache"], dict):
            cache = CACHE_BUILDER_REGISTRY.get(name=paras["cache"]["name"])(**paras["cache"].get("paras", dict()))
        else:
            cache = paras["cache"]

        self.paras = paras
        self.cache = cache  # type:Cache_Base

    def _write_of_cache(self, key, value):
        """
            向缓存中新增不存在的条目
        """
        #
        self.cache.write(key=key, value=value)

    def _remove_of_cache(self, key):
        """
            从缓存中删除存在的条目
        """
        self.cache.remove(key=key)

    def _read_of_cache(self, key):
        """
            读取缓存中 已经存在的 条目
        """
        return self.cache.read(key=key)

    def add(self, key, value, b_allow_overwrite=True):
        """
            以 key 为查询键，将 value 添加到缓存中

            参数:
                key:
                value:
                b_allow_overwrite:      <boolean> 是否允许覆写缓存中已有的条目
                                            默认为 True
        """
        # 判断是否需要进行覆写
        if self.cache.has(key=key):
            if id(value) != id(self.cache.read(key=key)):
                if b_allow_overwrite:
                    self._remove_of_cache(key=key)
                else:
                    raise KeyError(f'key: {key} already exists, modification of existing entries is prohibited')
            else:
                return
        # 记录到缓存
        self._write_of_cache(key=key, value=value)

    def get(self, key, b_add_if_not_found=False, default_factory=None, **kwargs):
        """
            获取 key 对应的值

            参数:
                key:                    <hashable>
                default:                默认值
                                            当 key 在缓存中不存在时返回
                default_factory:        <callable> 用于产生默认值的函数
                                            当 key 在缓存中不存在时返回该函数的结果
                                            使用该参数相对于 default 能延迟默认值的产生（如果不需要用到默认值就不生成），提高效率
                        注意！！上面两个参数同时指定时，将以前者为准。
                b_add_if_not_found:     <boolean> 当 key 在缓存中不存在时，是否添加到缓存中
                                            默认为 False
        """
        if self.cache.has(key=key):
            value = self._read_of_cache(key=key)
        elif "default" in kwargs or callable(default_factory):
            value = kwargs["default"] if "default" in kwargs else default_factory()
            if b_add_if_not_found:
                self._write_of_cache(key=key, value=value)
        else:
            raise KeyError(key)
        return value

    def pop(self, key):
        """
            从缓存中删除 key 对应的条目，并返回该条目的值
        """
        if self.cache.has(key=key):
            value = self._read_of_cache(key=key)
            self._remove_of_cache(key=key)
        else:
            raise KeyError(key)
        return value

    def has(self, key):
        """
            判断 key 是否在缓存中
                注意！！不会更新 metadata
        """
        return self.cache.has(key=key)

    def clear(self):
        self.cache.clear()

    # ---------------------- 用于保存和加载状态 ---------------------- #
    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.cache.load_state_dict(state_dict=state_dict["cache"])

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"cache": self.cache.state_dict(b_deepcopy=False)}
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp

    def __len__(self):
        return len(self.cache)

    def __contains__(self, key):
        return self.has(key)
