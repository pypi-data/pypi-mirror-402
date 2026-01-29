import pytest
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.computer_science.algorithm.cache_manager.cache import Cache_Base
from kevin_toolbox.computer_science.algorithm.cache_manager.variable import CACHE_BUILDER_REGISTRY


def test_memo_cache():
    print("test Memo_Cache")

    cache = CACHE_BUILDER_REGISTRY.get(name=":in_memory:Memo")()  # type: Cache_Base

    # 读写
    cache.write(key="1", value=1)
    cache[2] = "2"
    check_consistency(cache["1"], 1)
    check_consistency(cache.read(2), "2")
    # 禁止重复写入
    with pytest.raises(KeyError):
        cache.write(key="1", value=2)
    # 禁止读取/删除不存在条目
    with pytest.raises(KeyError):
        cache.read(key=1)
    with pytest.raises(KeyError):
        cache.remove(key=1)

    # 容量判断
    check_consistency(len(cache), 2)

    # 删除与命中判断
    check_consistency(cache.has("1"), True)
    check_consistency(cache.has(2), True)
    cache.remove(2)
    check_consistency(cache.has(2), False)

    # 清空
    cache.clear()
    check_consistency(len(cache), 0)


def test_array_cache():
    print("test Array_Cache")
    block_size = 1000000
    cache = CACHE_BUILDER_REGISTRY.get(name=":in_memory:Array")(
        block_size=block_size,
        value_names=["d", "f", "u", "i"],
        value_types=["object", "np.float32", "<U100", "int"]
    )  # type: Cache_Base

    # 读写
    v_1 = {"d": {2: 1, 1: 2}, "f": 3.4, "u": "123", "i": 12}
    v_2 = {"d": [1, 2, 3], "u": "abc", "i": 2}
    cache.write(key=1, value=v_1)
    cache[2000001] = v_2
    check_consistency(cache[1], v_1)
    check_consistency({k: v for k, v in cache.read(2000001).items() if k in v_2}, v_2)
    # 禁止重复写入
    with pytest.raises(KeyError):
        cache.write(key=1, value=v_2)
    # 禁止读取/删除不存在条目
    with pytest.raises(KeyError):
        cache.read(key=3)
    with pytest.raises(KeyError):
        cache.read(key=-1)
    with pytest.raises(KeyError):
        cache.remove(key=10)

    # 容量判断
    check_consistency(cache.occupation, block_size * 2)
    check_consistency(len(cache), 2)

    # 删除与命中判断
    check_consistency(cache.has(1), True)
    check_consistency(cache.has(2000001), True)
    cache.remove(2000001)
    check_consistency(cache.has(2000001), False)
    check_consistency(len(cache), 1)

    # 自动删除空 block
    cache.paras["b_drop_empty_block"] = True
    cache.remove(1)
    check_consistency(cache.occupation, block_size * 1)
    check_consistency(len(cache), 0)

    # 清空
    cache.clear()
    check_consistency(cache.occupation, 0)
    check_consistency(len(cache), 0)
