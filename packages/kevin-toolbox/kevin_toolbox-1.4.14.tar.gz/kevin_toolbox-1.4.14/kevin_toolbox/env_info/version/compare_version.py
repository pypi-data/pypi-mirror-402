import numpy as np
from .parse_version import parse_version_string_to_array as parse_to_array


def compare_version(v_0, operator, v_1, **kwargs):
    """
        在两个版本号之间比较大小

        参数：
            v_0, v_1:               <array of integers / string of version>
            operator：               比较符
                                        支持的取值： "==", ">=", "<=", ">", "<"
        可选参数：
            mode：                   对齐方式
                                        "long"（默认）： 以 v_0, v_1 中较长的为基准进行对齐，对于较短的版本号，缺省部分将补 0
                                        "short"： 以较短的为基准进行对齐，对于较长的版本号，多余部分直接截断
                                        （建议选用 "long"，因为对于无法解释的部分 version，parse_to_array()
                                        默认返回 [..., -1, ...]，此时如果使用 "short" 可能引发意外的错误）
            sep：                    分隔符
                                        对于string类型的版本号，默认使用"."作为分隔符，但是也可以在 kwargs 中通过 sep 指定，
                                        具体参考 parse_to_array()
        返回：
            boolean 比较结果
    """
    assert operator in {"==", ">=", "<=", ">", "<"}
    v_0, v_1 = map(lambda x: parse_to_array(x, **kwargs) if isinstance(x, (str,)) else x, [v_0, v_1])
    v_0, v_1 = map(lambda x: np.array(x, dtype=int).reshape(-1), [v_0, v_1])
    mode = kwargs.get("mode", "long")
    assert mode in ["long", "short"]

    if mode == "long":
        gap = np.zeros(shape=max(len(v_0), len(v_1)))
        gap[:len(v_0)] += v_0
        gap[:len(v_1)] -= v_1
    else:
        gap = np.zeros(shape=min(len(v_0), len(v_1)))
        gap += v_0[:len(gap)]
        gap -= v_1[:len(gap)]
    first_larger_index = np.argmax(gap > 0) if np.any(gap > 0) else len(gap)
    first_smaller_index = np.argmax(gap < 0) if np.any(gap < 0) else len(gap)
    if first_larger_index == first_smaller_index:
        res = "="
    elif first_larger_index < first_smaller_index:
        res = ">"
    else:
        res = "<"

    return res in operator


if __name__ == '__main__':
    print(compare_version([1, 2, 3], ">=", [1, 3]))
    print(compare_version("1.10.0a0", ">", "1.2"))
    print(compare_version("1.10.0a0", "<=", "1.2"))
