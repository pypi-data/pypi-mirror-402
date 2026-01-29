import os
import shutil
from kevin_toolbox.patches.for_os import remove


def copy(src, dst, follow_symlinks=True, remove_dst_if_exists=False):
    """
        复制文件/文件夹/软连接

        参数：
            follow_symlinks:        <boolean> 是否跟随符号链接
                                    对于 src 是软连接或者 src 指向的目录下具有软连接的情况，
                                        当设置为 True 时，会复制所有链接指向的实际文件或目录内容。
                                        当设置为 False 时，则仅仅软连接本身，而不是指向的内容
                                    默认为 True
            remove_dst_if_exists:   <boolean> 当目标存在时，是否尝试进行移除
    """
    assert os.path.exists(src), f'failed to copy, src not exists: {src}'
    if remove_dst_if_exists:
        remove(path=dst, ignore_errors=True)
    assert not os.path.exists(dst), f'failed to copy, dst exists: {dst}'

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src):
        if not follow_symlinks and os.path.islink(src):
            # 如果是符号链接，并且我们跟随符号链接，则复制链接本身
            os.symlink(os.readlink(src), dst)
        else:
            # 否则，递归复制目录
            shutil.copytree(src, dst, symlinks=not follow_symlinks)
    else:
        # 复制文件
        shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
