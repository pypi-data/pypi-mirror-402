import numpy as np
from .parse_version import parse_version_string_to_array as parse_to_array


def sort_version_ls(version_ls, reverse=False, **kwargs):
    """
        对版本号组成的列表 version_ls 进行排序
            支持字符串形式或者数字列表/元组形式的版本号进行混合排序，
            比如： version_ls=["0.10.7", (0, 7), [0, 7, 5]]
            在排序后将得到： [(0, 7), [0, 7, 5], "0.10.7"]

        参数：
            version_ls:             <list of strings/arrays>
            reverse:                <boolean>
                                        默认为 False 表示从小到大排列，当设置为 True 时则反序。
        可选参数：
            mode：                   对齐方式
                                        "long"（默认）： 以 version_ls 中较长的版本号为基准进行对齐，对于较短的版本号，缺省部分将补 0
                                        "short"： 以较短的为基准进行对齐，对于较长的版本号，多余部分直接截断
                                        （建议选用 "long"，因为对于无法解释的 version，parse_to_array()
                                        默认返回 [0]，此时如果使用 "short" 可能引发意外的错误）
            sep：                    分隔符
                                        对于string类型的版本号，默认使用"."作为分隔符，但是也可以在 kwargs 中通过 sep 指定，
                                        具体参考 parse_to_array()
        返回：
            boolean 比较结果
    """
    assert isinstance(version_ls, (list, tuple,))
    mode = kwargs.get("mode", "long")
    assert mode in ["long", "short"]

    value_ls = []
    length_ls = []
    for version in version_ls:
        value = parse_to_array(version, **kwargs) if isinstance(version, (str,)) else version
        assert isinstance(value, (list, tuple, np.ndarray,))
        value_ls.append(list(value))
        length_ls.append(len(value))

    if mode == "long":
        target = max(length_ls)
        value_ls = [i + [0] * (target - l) for i, l in zip(value_ls, length_ls)]
    else:
        target = min(length_ls)
        value_ls = [i[:target] for i in value_ls]
    # sort
    pairs_ls = sorted(list(zip(value_ls, version_ls)), key=lambda x: x[0], reverse=reverse)
    #
    res = [i for _, i in pairs_ls]
    return res
