import os
from kevin_toolbox.patches.for_os import walk


def find_files_in_dir(input_dir, suffix_ls=None, b_relative_path=True, b_ignore_case=True):
    """
        找出目录下带有给定后缀的所有文件的生成器
            主要利用了 for_os.walk 中的过滤规则进行实现

        参数：
            suffix_ls:          <list/tuple of str> 可选的后缀
            b_relative_path:    <bool> 是否返回相对路径
            b_ignore_case:      <bool> 是否忽略大小写
    """
    if suffix_ls is not None:
        suffix_ls = tuple(set(suffix_ls))
        suffix_ls = tuple(map(lambda x: x.lower(), suffix_ls)) if b_ignore_case else suffix_ls
        for root, dirs, files in walk(top=input_dir, topdown=True,
                                      ignore_s=[{
                                          "func": lambda _, b_is_symlink, path: b_is_symlink or not (
                                                  path.lower() if b_ignore_case else path).endswith(suffix_ls),
                                          "scope": ["files", ]
                                      }]):
            for file in files:
                file_path = os.path.join(root, file)
                if b_relative_path:
                    file_path = os.path.relpath(file_path, start=input_dir)
                yield file_path
    else:
        for root, dirs, files in walk(top=input_dir, topdown=True):
            for file in files:
                file_path = os.path.join(root, file)
                if b_relative_path:
                    file_path = os.path.relpath(file_path, start=input_dir)
                yield file_path
