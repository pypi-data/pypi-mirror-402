import os
import optuna
from enum import Enum
from kevin_toolbox.patches.for_os import remove


class Storage_Type(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"


def build_storage(mode, b_clear_before_create=False, **kwargs):
    """
        构建数据库实例

        参数：
            mode:                       <str> 数据库的种类
                目前支持以下几种模式。当 mode 设定为以下值时：

                - "sqlite"（python自带库，不需要额外环境配置，但不支持并行化）
                    还需要以下参数：
                        output_dir:     <path> 数据库文件保存目录
                        db_name:        <str> 数据库文件名称

                - "mysql"（需要按照 https://zhuanlan.zhihu.com/p/670547423 中进行配置，支持并行化）
                    还需要以下参数：
                        host:           <str> 主机名
                                            默认为 'localhost'
                        user:           <str> 用户名
                                            默认为 'root'
                        password:       <str> 登录密码
                                            默认缺省不指定
                        db_name:        <str> 数据库名
                        port:           <int> 端口
                                            默认为 3306

            其他共有的参数为：
                b_clear_before_create:  <boolean> 在创建前是否尝试清除已有数据库
                                            默认为 False。
                                            注意！！当进行并行化时，建议最多在主进程中设置一次 True，以免多个进程反复删除数据库引发错误。
    """
    mode = Storage_Type(mode)

    # 构建URI
    if mode is Storage_Type.SQLITE:
        assert "output_dir" in kwargs, \
            f'for mode "sqlite", please specify output_dir'
        file_path = os.path.join(kwargs["output_dir"], kwargs.get("db_name", "study.db"))
        url = f'sqlite:///{file_path}'
        #
        os.makedirs(kwargs["output_dir"], exist_ok=True)
        if b_clear_before_create:
            remove(path=file_path, ignore_errors=True)
    else:  # mode is Storage_Type.MYSQL
        assert "db_name" in kwargs, \
            f'for mode "mysql", please specify db_name'
        kwargs.setdefault("host", "localhost")
        kwargs.setdefault("user", "root")
        kwargs.setdefault("password", "")
        kwargs.setdefault("port", 3306)
        url = f'mysql+pymysql://{kwargs["user"]}:{kwargs["password"]}@' \
              f'{kwargs["host"]}/{kwargs["db_name"]}'
        #
        try:
            import pymysql
        except ImportError:
            raise ImportError('for mode "mysql", please install pymysql')
        conn = pymysql.connect(host=kwargs["host"], user=kwargs["user"], password=kwargs["password"],
                               port=kwargs["port"])
        cursor = conn.cursor()
        if b_clear_before_create:
            cursor.execute(f'DROP DATABASE IF EXISTS {kwargs["db_name"]}')
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS {kwargs["db_name"]}')
        cursor.close()
        conn.close()

    return optuna.storages.RDBStorage(url)
