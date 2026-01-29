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

ILLEGAL_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*]')


def find_illegal_chars(file_name, b_is_path=False):
    """
        找出给定的文件名/路径中出现了哪些非法符号
            所谓非法符号是指在特定系统（win/mac等）中文件名不允许出现的字符，
            不建议在任何系统下使用带有这些符号的文件名，即使这些符号在当前系统中是合法的，
            以免在跨系统时出现兼容性问题

        参数：
            file_name:      <str>
            b_is_path:      <bool> 是否将file_name视为路径
                                默认为 False
                                当设置为 True 时，将会首先将file_name分割，再逐级从目录名中查找
    """
    global ILLEGAL_CHARS_PATTERN

    if b_is_path:
        temp = [i for i in file_name.split(os.sep, -1) if len(i) > 0]
    else:
        temp = [file_name]
    res = []
    for i in temp:
        res.extend(ILLEGAL_CHARS_PATTERN.findall(i))
    return res


if __name__ == '__main__':
    file_path = '//data0//b/<?>.md'
    print(find_illegal_chars(file_name=file_path, b_is_path=True))
    print(find_illegal_chars(file_name=file_path, b_is_path=False))
