import os
import re

ILLEGAL_CHARS = {
    '<': '＜',
    '>': '＞',
    ':': '：',
    '"': '＂',
    '/': '／',
    '\\': '＼',
    '|': '｜',
    '?': '？',
    '*': '＊'
}
ILLEGAL_CHARS_PATTERN = re.compile('|'.join(re.escape(char) for char in ILLEGAL_CHARS.keys()))


def replace_illegal_chars(file_name, b_is_path=False):
    """
        将给定的文件名/路径中的非法符号替换为合法形式
            所谓非法符号是指在特定系统（win/mac等）中文件名不允许出现的字符，
            不建议在任何系统下使用带有这些符号的文件名，即使这些符号在当前系统中是合法的，
            以免在跨系统时出现兼容性问题。

        参数：
            file_name:      <str>
            b_is_path:      <bool> 是否将file_name视为路径
                                默认为 False
                                当设置为 True 时，将会首先将file_name分割，再逐级处理目录名，最后合并为路径
    """
    if not b_is_path:
        res = _replace_illegal_chars(var=file_name)
    else:
        temp = file_name.split(os.sep, -1)
        res = os.path.join(*[_replace_illegal_chars(var=i) for i in temp if len(i) > 0])
        if len(temp[0]) == 0:
            res = os.sep + res
    return res


def _replace_illegal_chars(var):
    global ILLEGAL_CHARS_PATTERN
    return ILLEGAL_CHARS_PATTERN.sub(lambda m: ILLEGAL_CHARS[m.group(0)], var)


if __name__ == '__main__':
    file_path = 'data0//b/<?>.md'
    print(replace_illegal_chars(file_name=file_path, b_is_path=True))
    print(replace_illegal_chars(file_name=file_path, b_is_path=False))
