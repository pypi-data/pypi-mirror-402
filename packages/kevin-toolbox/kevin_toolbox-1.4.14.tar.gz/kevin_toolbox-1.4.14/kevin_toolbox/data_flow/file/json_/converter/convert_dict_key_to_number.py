def convert_dict_key_to_number(x):
    """
        尝试将字典中的所有 key 转换为数字
    """
    if isinstance(x, dict):
        res = dict()
        for k, v in x.items():
            try:
                k = int(k)
            except:
                try:
                    k = float(k)
                except:
                    pass
            res[k] = v
        return res
    else:
        return x


if __name__ == '__main__':
    print(convert_dict_key_to_number({"123": 123, "-1": -1, "1.23": 1.23, "-1.000": -1.0, "1.2.3": None}))
