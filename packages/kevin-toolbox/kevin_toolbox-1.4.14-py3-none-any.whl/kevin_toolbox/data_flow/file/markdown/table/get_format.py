import warnings
from kevin_toolbox.data_flow.file.markdown.table import Table_Format


def get_format(content_s):
    res = None
    if isinstance(content_s, dict):
        if "orientation" in content_s and isinstance(content_s["orientation"], str):
            res = Table_Format.MATRIX
        elif len(content_s) > 0:
            v = list(content_s.values())[0]  # 是 get_format 而不是 check_format，所以只取第一个值进行判断就够了
            if isinstance(v, dict):
                res = Table_Format.COMPLETE_DICT
            elif isinstance(v, (list, tuple)):
                res = Table_Format.SIMPLE_DICT
    if res is None:
        warnings.warn(f'failed to get format from given content_s: {content_s}')
    return res
