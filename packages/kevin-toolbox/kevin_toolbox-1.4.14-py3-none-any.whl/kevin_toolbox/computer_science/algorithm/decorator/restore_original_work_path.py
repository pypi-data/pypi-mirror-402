import os
from functools import wraps


def restore_original_work_path(func):
    """
        装饰器，在运行函数 func 前备份当前工作目录，并在函数运行结束后还原到原始工作目录。
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        pwd_bak = os.getcwd()
        res = func(*args, **kwargs)
        os.chdir(pwd_bak)
        return res

    return wrap
