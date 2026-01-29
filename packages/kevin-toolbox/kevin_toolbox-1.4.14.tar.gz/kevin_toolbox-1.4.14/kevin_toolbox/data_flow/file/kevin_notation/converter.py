RAW_SETTINGS = dict(
    default=dict(
        read=lambda x: x,
        write=lambda x: f"{x}",
    ),
    int=dict(
        read=lambda x: int(eval(x)),
        write=lambda x: f"{int(x) if x is not None else None}",
    ),
    float=dict(
        read=lambda x: float(x.replace("None", "nan")),
    ),
    str=dict(
        read=lambda x: str(x),
    ),
    list=dict(
        read=lambda x: eval(deal_nan(x, None)),
    ),
)


def deal_nan(x, replace_with=None):
    x = x.replace("nan", str(replace_with))
    return x


SETTINGS = dict(
    read=dict(),
    write=dict()
)
for converter_name, item in RAW_SETTINGS.items():
    for k, v in item.items():
        SETTINGS[k][converter_name] = v


class Converter:
    def __init__(self, **kwargs):
        """
            获取具体的 converter
                converter is a dictionary-like data structure consisting of <string>:<func> pairs，
                用于根据指定数据类型选取适当的函数来处理输入数据

            参数：
                mode：           <string> 转换模式
                                    可选值：
                                        "read":     适用于 Kevin_Notation_Reader
                                        "write":    适用于 Kevin_Notation_Writer
        """
        # 默认参数
        paras = {
            # 必要参数
            "mode": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert paras["mode"] in ["read", "write"]

        self.paras = paras

    def get(self, key, **kwargs):
        """
            获取具体的 converter
                converter is a dictionary-like data structure consisting of <string>:<func> pairs，
                用于根据指定数据类型选取适当的函数来处理输入数据

            参数：
                key:            <string> 键
                use_default:    <boolean> 当无法查找到 key 对应的 converter 时，是否返回默认的 converter
                                    默认为 True
                                    当设置为 False 且遇到不存在的 key 时，将引起 KeyError 错误
                mode：           <string> 另外设定模式，而不使用初始化时默认设定的模式
        """

        # 默认参数
        paras = {
            "use_default": True,
            "mode": self.paras["mode"],
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(key, (str,))
        assert paras["mode"] in ["read", "write"]

        converter = SETTINGS[paras["mode"]].get(key, None)
        if converter is None:
            if paras["use_default"]:
                converter = SETTINGS[paras["mode"]].get("default")
            else:
                raise KeyError(f"the most recent CONVERTER does not support type {key}")

        return converter

    def __getitem__(self, key):
        """
            通过 self[] 调用 get()
        """
        return self.get(key)

    def keys(self):
        return SETTINGS[self.paras["mode"]].keys()

    def values(self):
        return SETTINGS[self.paras["mode"]].values()

    def len(self):
        return len(SETTINGS[self.paras["mode"]])

    def items(self):
        return SETTINGS[self.paras["mode"]].items()


CONVERTER_FOR_READER = Converter(mode="read")
CONVERTER_FOR_WRITER = Converter(mode="write")

if __name__ == '__main__':
    print(SETTINGS)

    converter_ = Converter(mode="read")

    print(converter_.get("float"))
    print(converter_["f"])
    print(converter_.keys())
