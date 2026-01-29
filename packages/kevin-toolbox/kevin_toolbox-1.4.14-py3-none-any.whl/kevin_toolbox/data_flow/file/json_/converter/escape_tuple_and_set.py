def escape_tuple_and_set(x):
    """
        将 tuple 和 set 进行转义
            转义：     x ==> f"<eval>{x}"
            反转义：   f"<eval>{x}" ==> x

        为什么要进行转义？
            由于 json 中会将 tuple 作为 list 进行保存，同时也无法保存 set，因此在保存过程中会丢失相应信息。
    """
    if isinstance(x, (tuple, set,)) or (isinstance(x, (str,)) and x.startswith("<eval>")):
        return f'<eval>{x}'
    else:
        return x


if __name__ == '__main__':
    print(escape_tuple_and_set((1, 2, "\'1\'")))
    # <eval>(1, 2, "'1'")
    print(escape_tuple_and_set({"1", (1, 2, 3), 233}))
    # <eval>{'1', 233, (1, 2, 3)}

    print(escape_tuple_and_set("<eval>233"))
    # <eval><eval>233
