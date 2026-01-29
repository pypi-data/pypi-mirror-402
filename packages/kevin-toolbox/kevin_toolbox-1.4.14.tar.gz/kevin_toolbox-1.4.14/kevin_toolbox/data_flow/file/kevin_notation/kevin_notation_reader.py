import os
from kevin_toolbox.data_flow.core.reader import File_Iterative_Reader
from kevin_toolbox.data_flow.file.kevin_notation.converter import Converter, CONVERTER_FOR_READER


def set_comment_flag_to_reader(reader, comment_flag):
    if comment_flag is not None and isinstance(comment_flag, str) and len(comment_flag) > 0:
        reader.paras["filter_"] = lambda x: x != "\n" and not x.startswith(comment_flag)  # 去除注释
        reader.paras["map_func"] = lambda x: x.rsplit("\n", 1)[0].split(comment_flag, 1)[0]


class Kevin_Notation_Reader:
    """
        遵守 kevin_notation 格式的数据文本读取器（格式要求参见本模块下的 readme）
            支持分批次读取文件内容
    """

    def __init__(self, **kwargs):
        """
            设定关键参数

            必要参数：
                file_path:          <string> 文件路径
                file_obj:           <file object> 文件对象
                    以上参数2选一，具体参见 File_Iterative_Reader
            读取相关参数：
                chunk_size:         <integer> 每次读取多少行数据
                beg：                <integer> 开始读取的位置
                                                默认为0
                converter:          <instance of kevin_toolbox.Converter> converter is a dictionary-like data structure
                                                consisting of <string>:<func> pairs，
                                                用于根据指定数据类型选取适当的函数来处理输入数据。
        """

        # 默认参数
        paras = {
            # 必要参数
            "file_path": None,
            "file_obj": None,
            # 读取相关参数
            "chunk_size": 100,
            "beg": 0,
            "converter": CONVERTER_FOR_READER,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        #   file_path 和 file_obj 交给 File_Iterative_Reader 校验
        assert isinstance(paras["chunk_size"], (int,)) and (paras["chunk_size"] > 0 or paras["chunk_size"] == -1)
        assert isinstance(paras["beg"], (int,)) and paras["beg"] >= 0
        assert isinstance(paras["converter"], (Converter, dict,))

        self.paras = paras

        # 读取开头
        self.reader = File_Iterative_Reader(file_path=self.paras["file_path"], file_obj=self.paras["file_obj"],
                                            pre_jump_size=self.paras["beg"],
                                            filter_=lambda x: x != "\n",  # 去除注释
                                            map_func=lambda x: x.rsplit("\n", 1)[0],
                                            drop=False)
        # kevin_notation
        offset = self.read_head(reader=self.reader, head="# --kevin_notation--")
        # metadata
        offset += self.read_head(reader=self.reader, head="# --metadata--")
        #
        self.metadata, count = self.read_metadata(reader=self.reader, converter=self.paras["converter"])
        offset += count

        temp = {k: v for k, v in self.reader.paras.items() if
                k in ["file_path", "file_obj", "filter_", "map_func", "drop"]}
        del self.reader

        # 读取内容
        comment_flag = self.metadata.get("comment_flag", None)
        temp["pre_jump_size"] = self.paras["beg"] + offset
        if comment_flag is not None and isinstance(comment_flag, str) and len(comment_flag) > 0:
            temp["pre_jump_size"] -= 1  # 将自动忽略注释那一行，因此需要减去1
        self.reader = File_Iterative_Reader(**temp)

        # contents
        self.read_head(reader=self.reader, head="# --contents--")

    # ------------------------------------ read head ------------------------------------ #

    @staticmethod
    def read_head(reader, head, try_times=10):
        reader.paras.update(dict(
            chunk_size=1,
        ))
        #
        for count in range(1, try_times + 1):
            line = next(reader)[0]
            if line.startswith("#"):
                assert line.startswith(head), \
                    f"format of {head} is wrong!"
                return count
        raise Exception(f"can't find {head} after {try_times} attempts")

    # ------------------------------------ read metadata ------------------------------------ #

    @staticmethod
    def read_metadata(reader, converter):
        reader.paras.update(dict(
            chunk_size=2,
        ))
        key, sep = next(reader)
        assert key.startswith("# sep"), \
            f"format of metadata is wrong!"  # 开头第一个参数必须是 sep
        res = dict(sep=sep)
        #
        count = 2
        for chunk in reader:
            if len(chunk) == 2:
                key, value = chunk
            else:
                key, value = chunk[0], None
            assert key.startswith("# "), f"{key}:{value}"
            if key.startswith("# --contents--"):
                break
            temp_ls = [i.strip() for i in key.split(' ', 2)]
            assert len(temp_ls) >= 2
            #
            count += 2
            #
            key = temp_ls[1]
            #
            paras_dict = dict()
            if len(temp_ls) > 2:
                paras = temp_ls[2]
                assert paras.startswith("(") and paras.endswith(")")
                paras = paras[1:-1]
                paras_ls = [i.split("=", 1) for i in paras.split(",", -1)]
                paras_dict.update({k: v for (k, v) in paras_ls})
            sep = paras_dict.get("sep", res["sep"])
            #
            value = value.split(sep, -1)
            if len(value) == 1 and key not in ["column_name", "column_type"]:
                value = value[0]
            #
            if key == "comment_flag":
                set_comment_flag_to_reader(reader=reader, comment_flag=value)
            #
            res[key] = value

        # 最后检验内容
        # 与 column 数量相关的字段是否相互一致
        num_ls = [len(res[key]) for key in ["column_name", "column_type"] if key in res]
        num_ls.extend([int(res[key]) for key in ["column_num"] if key in res])
        assert len(set(num_ls)) <= 1, f"{num_ls}"
        #
        if len(num_ls) > 0:
            res["column_num"] = num_ls[0]
        #
        if "column_type" in res:
            unknown_types = set(res["column_type"]).difference(set(converter.keys()))
            if len(unknown_types) > 0:
                print(f"Warning: There are unknown types {unknown_types} in column_type. "
                      f"Currently supported types are {set(converter.keys())}")

        return res, count

    # ------------------------------------ read contents ------------------------------------ #

    @staticmethod
    def read_contents(reader, chunk_size, metadata, converter):
        """
            读取 contents，并根据 metadata 对其进行解释
        """
        reader.paras.update(dict(
            chunk_size=chunk_size,
        ))
        #
        res = None
        chunk = next(reader)
        # 解释
        for line in chunk:
            value_ls = line.split(metadata["sep"])
            if "column_type" in metadata:
                assert len(value_ls) == len(metadata["column_type"])
                type_ls = metadata["column_type"]
            else:
                # use default converter
                type_ls = ["default"] * len(value_ls)
            value_ls = [converter[type_](value) for type_, value in zip(type_ls, value_ls)]
            if res is None:
                res = [[] for _ in range(len(value_ls))]
            for i, value in enumerate(value_ls):
                res[i].append(value)
        # 整理
        if res is not None:
            column_name = metadata.get("column_name", list(range(len(res))))
            assert len(column_name) == len(res)
            res = {k: res[i] for i, k in enumerate(column_name)}
        return res, len(chunk)

    # ------------------------------------ magic func ------------------------------------ #

    def __next__(self):
        contents, len_ = self.read_contents(reader=self.reader, chunk_size=self.paras["chunk_size"],
                                            metadata=self.metadata, converter=self.paras["converter"])
        if len_ == 0:
            raise StopIteration
        else:
            return contents

    def __iter__(self):
        return self

    # with 上下文管理器
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self

    def __del__(self):
        try:
            del self.paras, self.metadata, self.reader
        except Exception as e:
            print(e)
