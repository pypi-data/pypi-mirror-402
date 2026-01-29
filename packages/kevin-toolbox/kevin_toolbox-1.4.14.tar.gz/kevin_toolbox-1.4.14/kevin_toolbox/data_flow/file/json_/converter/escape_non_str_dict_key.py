def escape_non_str_dict_key(x):
    """
        将字典中的所有非字符串的 key 进行转义
            转义：     key ==> f"<eval>{key}"
            反转义：   f"<eval>{key}" ==> key

        为什么要进行转义？
            由于 json 中要求字典的键必须使用字符串进行保存，因此在保存过程中会丢失相应信息。
    """
    if isinstance(x, dict):
        res = dict()
        for k, v in x.items():
            if not isinstance(k, (str,)) or k.startswith("<eval>"):
                k = f'<eval>{k}'
            res[k] = v
        return res
    else:
        return x


if __name__ == '__main__':
    print(escape_non_str_dict_key({123: 123, "<eval>-1.000": -1.0, None: None}))
    # {'<eval>123': 123, '<eval><eval>-1.000': -1.0, '<eval>None': None}
