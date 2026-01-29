from kevin_toolbox.data_flow.file.markdown.table import get_format, Table_Format


def padding_misaligned_values(content_s, padding_value=""):
    """
        将标题下长度不相等的 values 补齐
    """
    format_ = get_format(content_s)
    if format_ is Table_Format.COMPLETE_DICT:
        v_ls = [v["values"] for v in content_s.values()]
    elif format_ is Table_Format.SIMPLE_DICT:
        v_ls = list(content_s.values())
    else:
        raise ValueError(f"unsupported format {format_}")

    len_ls = [len(v) for v in v_ls]
    max_length = max(len_ls)
    if min(len_ls) != max_length:
        for v in v_ls:
            v.extend([padding_value] * (max_length - len(v)))

    return content_s
