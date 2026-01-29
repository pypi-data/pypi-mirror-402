import os
from collections import defaultdict
from enum import Enum


class Ignore_Scope(Enum):
    ROOT = "root"
    DIRS = "dirs"
    FILES = "files"


class Path_Ignorer:
    def __init__(self, ignore_s=None):
        self.ignore_s = defaultdict(list)
        try:
            if isinstance(ignore_s, (list, tuple)):
                for it in ignore_s:
                    for scope in it["scope"]:
                        scope = Ignore_Scope(scope)
                        self.ignore_s[scope].append(it["func"])
            elif isinstance(ignore_s, (dict,)):
                for k, v in ignore_s.items():
                    self.ignore_s[Ignore_Scope(k)].extend(v)
        except:
            raise ValueError(f'invalid ignore_s, got a {ignore_s}')

    def __call__(self, scope, *args, **kwargs):
        for func in self.ignore_s[scope]:
            if func(*args, **kwargs):
                return True
        return False

    def __len__(self):
        return len(self.ignore_s)


def walk(top, topdown=True, onerror=None, followlinks=False, ignore_s=None):
    """
        在 os.walk() 的基础上增加了以下功能
            - 可以通过 ignore_s 参数来排除特定的目录和文件

        参数：
            （对于参数 top,topdown,onerror,followlinks，其用法与 os.walk() 完全相同）
            top:                <path> 要遍历的目录
            topdown:            <boolean> 是否从浅到深遍历
                                    默认为 True，优先遍历完浅层目录
            onerror:            <callable> 当遇到异常时，会调用该函数
            followlinks:        <boolean> 是否遍历软链接目录
                                    默认为 False，不对软链接进行进一步遍历
            ignore_s:           <list/tuple of dict or dict> 排除规则
                                    有两种输入方式：

                                    方式 1 <list/tuple of dict>：
                                        列表中每个字典需要具有以下键值对：
                                            "scope":    <list/tuple of str> 该规则的作用范围
                                                            可选值，及（满足规则时）对应效果：
                                                                "root":         不遍历满足规则的目录
                                                                "dirs":         将返回的三元组中第二个 dirs 部分中满足规则的部分移除
                                                                "files":        将返回的三元组中第三个 files 部分中满足规则的部分移除
                                            "func":     <callable> 排除规则
                                                            当调用该函数的返回值为 True 时，执行排除。
                                                            函数类型为 def(b_is_dir, b_is_symlink, path): ...
                                                            其中：
                                                                b_is_dir        是否是目录
                                                                b_is_symlink    是否是软链接
                                                                path            输入是对于作用范围 "root"，输入的直接就是 root，
                                                                                对于作用范围 "dirs"，输入是 dirs 中的每个元素和 root 组成的绝对路径，
                                                                                对于作用范围 "files"，输入是 files 中的每个元素和 root 组成的绝对路径。
                                            注意：
                                                - 当有多个规则时，只要满足其一即会进行排除。
                                                - 任何规则都不会对 top 目录进行过滤，亦即对 top 的遍历是必然的。不能通过设定某个 top 满足的规则来停止对 top 的遍历。
                                        比如，通过下面的规则就可以实现不对 basename 为 "test" 和 "temp" 的目录进行遍历和输出，
                                        同时只保留非软连接的 .png 和 .jpg 文件：
                                            [
                                                {
                                                    "func": lambda _, __, path: os.path.basename(path) in ["temp", "test"],
                                                    "scope": ["root", "dirs"]
                                                },
                                                {
                                                    "func": lambda _, b_is_symlink, path: b_is_symlink or not path.endswith((".png",".jpg")),
                                                    "scope": ["files", ]
                                                }
                                            ]

                                    方式 2 <dict>:
                                        一个以 scope 为键，func 为值的字典。
                                        延续上面的例子，其另一种等效形式为：
                                            {
                                                "root": [
                                                    lambda _, __, path: os.path.basename(path) in ["temp", "test"],
                                                ],
                                                "dirs": [
                                                    lambda _, __, path: os.path.basename(path) in ["temp", "test"],
                                                ],
                                                "files": [
                                                    lambda _, b_is_symlink, path: b_is_symlink or not path.endswith((".png",".jpg")),
                                                ]
                                            }

                                    方式 3 <Path_Ignorer>:
                                        根据 ignore_s 构建的 Path_Ignorer

    """
    # 根据 ignore_s 构建 Path_Ignorer
    path_ignorer = ignore_s if isinstance(ignore_s, (Path_Ignorer,)) else Path_Ignorer(ignore_s=ignore_s)

    #
    yield from __walk(top, topdown, onerror, followlinks, path_ignorer)


def __walk(top, topdown, onerror, followlinks, path_ignorer):
    #
    top = os.fspath(top)
    dirs, files = [], []
    walk_dirs = []

    try:
        scandir_it = os.scandir(top)
    except OSError as error:
        if onerror is not None:
            onerror(error)
        return

    with scandir_it:
        while True:
            try:
                try:
                    entry = next(scandir_it)
                except StopIteration:
                    break
            except OSError as error:
                if onerror is not None:
                    onerror(error)
                return

            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False

            if is_dir:
                dirs.append(entry.name)
                walk_dirs.append(os.path.join(top, entry.name))
            else:
                files.append(entry.name)

    # 过滤
    if len(path_ignorer) > 0:
        for it_ls, scope in zip([walk_dirs, dirs, files], [Ignore_Scope.ROOT, Ignore_Scope.DIRS, Ignore_Scope.FILES]):
            for i in reversed(range(len(it_ls))):
                path = os.path.join(top, it_ls[i]) if scope != Ignore_Scope.ROOT else it_ls[i]
                if path_ignorer(scope, scope != Ignore_Scope.FILES, os.path.islink(path), path):
                    it_ls.pop(i)

    #
    if topdown:
        yield top, dirs, files
        #
        for new_path in walk_dirs:
            if followlinks or not os.path.islink(new_path):
                yield from __walk(new_path, topdown, onerror, followlinks, path_ignorer)
    else:
        for new_path in walk_dirs:
            if followlinks or not os.path.islink(new_path):
                yield from __walk(new_path, topdown, onerror, followlinks, path_ignorer)
        #
        yield top, dirs, files
