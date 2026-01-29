import os
import shutil


def remove(path, ignore_errors=False):
    """
        移除文件/文件夹/软连接

        返回:
            boolean 是否成功
    """
    try:
        if os.path.islink(path):  # 移除软连接
            os.unlink(path)
        elif os.path.isfile(path):  # 移除文件
            os.remove(path)
        elif os.path.isdir(path):  # 移除文件夹
            shutil.rmtree(path=path, ignore_errors=False)
        else:
            raise FileNotFoundError(f'path: {path} not exists')
        return True
    except Exception as e:  # 删除失败
        if not ignore_errors:
            raise Exception(e)
        return False


if __name__ == '__main__':
    remove(path="233.txt", ignore_errors=True)
