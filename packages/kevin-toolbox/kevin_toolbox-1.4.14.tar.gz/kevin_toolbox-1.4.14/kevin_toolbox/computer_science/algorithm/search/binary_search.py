def binary_search(ls, value, is_sorted=False):
    """
        二分法查找
            返回给定的 value 在已经排序好的数组 ls 中，按照顺序应该插入到哪个 index 位置上
            比如 ls=[0, 1, 2, 2, 3], value=2 则返回适合插入的第一个位置 index=2

        参数:
            ls:             <list/tuple>
            value:
            is_sorted:      <boolean> 数组是否已经按从小到大进行排序

        返回：
            index
    """
    assert isinstance(ls, (list, tuple,))
    if not is_sorted:
        ls = sorted(ls)
    return _binary_search(ls=ls, value=value, beg=0, end=len(ls) - 1)


def _binary_search(ls, value, beg, end):
    if beg > end:
        return beg
    mid = (beg + end) // 2
    if value <= ls[mid] and (mid - 1 < 0 or ls[mid - 1] < value):
        return mid
    elif value < ls[mid]:
        return _binary_search(ls, value, beg=beg, end=mid - 1)
    else:
        return _binary_search(ls, value, beg=mid + 1, end=end)
