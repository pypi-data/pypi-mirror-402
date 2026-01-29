def parse_version_string_to_array(string, **kwargs):
    """
        将版本的字符串转换为数组的形式

        参数：
            string:                 string of version
            sep：                    分隔符
        工作流程：
            string "1.2.3"  == sep '.' ==> array [1, 2, 3]
            注意：对于分割后包含非整数的 string，返回 -1，例如：
            string "1.2_3"  == sep '_' ==> array [-1, 3]
        返回：
            array:                 array of version
    """
    sep = kwargs.get("sep", '.')
    assert isinstance(string, (str,))

    array = string.split(sep, -1)
    array = [int(v) if v.isdigit() else -1 for v in array]
    return array


if __name__ == '__main__':
    print(parse_version_string_to_array("1.2.3"))
    print(parse_version_string_to_array("1.2_3", sep="_"))
