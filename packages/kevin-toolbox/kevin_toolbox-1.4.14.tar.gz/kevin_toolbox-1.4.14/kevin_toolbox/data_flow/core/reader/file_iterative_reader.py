import os
import copy


class File_Iterative_Reader:
    """
        分批次读取文件内容的迭代器
        a get_generator to read the file piece by piece
    """

    def __init__(self, **kwargs):
        """
            设定关键参数
            必要参数：
                file_path:  文件路径
                file_obj:   文件对象
                    注意！！以上两个参数指定其一即可，同时指定时候，以后者为准。
            读取模式相关参数：
                paras_for_open:     open() 函数的补充参数
                mode:       读取模式，默认为 "lines"
                                "lines"：  按行数计算批次大小
                                "bytes"：  按字节数计算
                    注意！！以上两个参数在指定了 file_obj 参数后将失效。
                chunk_size: 批次大小
                                默认为 1k
                                当为-1时，读取整个文件
                jump_size:  以后每读取一个批次就跳过的大小（每个chunk之间的gap）
                                默认为 0
                                当为-1时，跳过整个文件
                pre_jump_size: 在开始读取文件前跳过的大小
                                默认为 0
                                当为-1时，跳过整个文件
                loop_num:   循环次数
                                默认为 1 循环一次
                                小于1时，比如0、-1表示无限循环
            处理相关参数：
                drop:       丢弃不足 chunk_size 的部分。
                                默认为 False 不开启
                filter_:     过滤函数，返回一个boolean值。
                                对读取的内容进行过滤，只有过滤通过的内容才会添加到结果。
                                默认跳过空行
                map_func:   后处理函数（逐元素处理）。
                                对读取的 "lines" 中的每行或者 "bytes" 中的每个字符进行什么处理。
                                对于 "lines"，默认使用strip()去除首、尾的空格、换行符。
                                对于 "bytes"，默认不进行任何处理。
                convert_func: 后处理函数（对整体进行处理）。
                                对 "lines" 或者 "bytes" 中整体的内容进行什么处理。
                                默认不进行任何处理。
                处理流程： ==> filter_ ==> drop ==> map_func ==> convert_func
            返回：
                类型取决于 mode（"lines"返回的是列表，"bytes"是单个字符串） 以及 map_func 的处理结果
        """

        # 默认参数
        paras = {
            # 必要参数
            "file_path": None,
            "file_obj": None,
            # 读取模式相关参数
            "paras_for_open": dict(mode="r", encoding='utf-8'),
            "mode": "lines",
            "chunk_size": 1000,
            "jump_size": 0,
            "pre_jump_size": 0,
            "loop_num": 1,
            # 处理相关参数
            "drop": False,
            "filter_": lambda x: x != "\n",
            "map_func": lambda x: x.strip(),
            "convert_func": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        #
        mode = paras["mode"]
        assert mode in ["lines", "bytes"]
        paras["chunk_size"] = int(paras["chunk_size"])
        paras["loop_num"] = int(paras["loop_num"]) - 1

        # 获取文件对象
        if paras["file_obj"] is None:
            assert isinstance(paras["file_path"], (str,)) and os.path.isfile(paras["file_path"]), \
                Exception(f'Error: file {paras["file_path"]} not exists!')
            #
            assert isinstance(paras["paras_for_open"], (dict,))
            self.file = open(paras["file_path"], **paras["paras_for_open"])
        else:
            # 拷贝对象，防止修改外部对象
            try:
                self.file = copy.deepcopy(paras["file_obj"])
            except:
                self.file = open(paras["file_obj"].name, mode=paras["file_obj"].mode)

        # 选择相应模式
        self.__read_func = {"lines": self.__read_lines, "bytes": self.__read_bytes}[mode]
        self.__jump_func = {"lines": self.__jump_lines, "bytes": self.__jump_bytes}[mode]

        self.now_in_beginning = True

        self.paras = paras

    def __next__(self):
        paras = self.paras
        while True:
            # 跳过开头部分
            if self.now_in_beginning:
                self.__jump_func(self.file, paras["pre_jump_size"], paras["filter_"])

            # 读取
            lines, end = self.__read_func(self.file, paras["chunk_size"],
                                          paras["filter_"], paras["map_func"], paras["convert_func"],
                                          paras["drop"])
            # 跳过
            self.__jump_func(self.file, paras["jump_size"], paras["filter_"])

            #
            if end:
                # 没有读到内容
                if not self.now_in_beginning and paras["loop_num"] != 0:
                    # 到达末尾，而且还有循环次数
                    # 就返回文档首部，尝试再次读取
                    self.file.seek(0)
                    self.now_in_beginning = True
                    paras["loop_num"] -= 1
                    continue
                else:
                    # 其他情况，比如：
                    #     在开头就读不到内容，是空文件
                    #     到达末尾却没有循环次数
                    # 则终止迭代
                    self.file.close()
                    raise StopIteration
            else:
                # 读到内容
                self.now_in_beginning = False
                break
        return lines

    @staticmethod
    def __read_lines(file, chunk_size, filter_, map_func, convert_func, drop):
        """
            按行读取文件中的 chunk_size 行
            返回：
                lines:      list，读取的内容
                end:        boolean，是否到文件末尾
        """
        lines = []
        while chunk_size < 0 or len(lines) < chunk_size:
            line = file.readline()
            # 到达文档最后
            if not line:
                break
            # 过滤失败
            if filter_ is not None and not filter_(line):
                continue
            # 添加
            lines.append(line)
        end = len(lines) == 0
        if not end:
            # 是否丢弃
            lines = [] if drop and len(lines) < chunk_size else lines
            # 后处理
            lines = list(map(map_func, lines)) if map_func is not None else lines
            lines = convert_func(lines) if convert_func is not None else lines
        return lines, end

    @staticmethod
    def __jump_lines(file, jump_size, filter_):
        """
            跳过 jump_size 行
            返回：
                count:      int，跳过的行数
                end:        boolean，是否到文件末尾
        """
        count = 0
        while jump_size < 0 or count < jump_size:
            line = file.readline()
            # 到达文档最后
            if not line:
                break
            # 过滤失败
            if filter_ is not None and not filter_(line):
                continue
            # 计数
            count += 1
        return count, count == 0

    @staticmethod
    def __read_bytes(file, chunk_size, filter_, map_func, convert_func, drop):
        """
            按字符数读取文件内容
            返回：
                bytes_:      string
                end:        boolean，是否到文件末尾
        """

        bytes_ = file.read(chunk_size)
        end = len(bytes_) == 0
        if not end:
            # 过滤
            bytes_ = '' if filter_ is not None and not filter_(bytes_) else bytes_
            # 是否丢弃
            bytes_ = '' if drop and len(bytes_) < chunk_size else bytes_
            # 后处理
            bytes_ = "".join([map_func(i) for i in bytes_]) if map_func is not None else bytes_
            bytes_ = convert_func(bytes_) if convert_func is not None else bytes_
        return bytes_, end

    @staticmethod
    def __jump_bytes(file, jump_size, filter_):
        """
            跳过 jump_size 个字符
            返回：
                count:      int，跳过的字符数
                end:        boolean，是否到文件末尾
        """
        bytes_ = file.read(jump_size)
        count = len(bytes_)
        return count, count == 0

    def __iter__(self):
        return self

    def __del__(self):
        try:
            del self.paras
            self.file.close()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    import numpy as np

    print("使用 file_path")
    reader = File_Iterative_Reader(file_path="test/test_data/test_data.txt", chunk_size=2, drop=True, loop_num=2,
                                   pre_jump_size=3, convert_func=lambda x: np.array(x))
    for i in reader:
        print(i)

    del reader

    print("使用 file_obj")
    reader = File_Iterative_Reader(
        file_obj=open("test/test_data/test_data.txt", "r"), chunk_size=2, drop=True, loop_num=2,
        pre_jump_size=3, convert_func=lambda x: np.array(x))
    for i in reader:
        print(i)

    del reader

    print("从字符串构建文件对象作为 file_obj")
    from io import StringIO

    file_obj = StringIO(initial_value=open("test/test_data/test_data.txt", "r").read())
    reader = File_Iterative_Reader(
        file_obj=file_obj, chunk_size=2, drop=True, loop_num=2,
        pre_jump_size=3, convert_func=lambda x: np.array(x))
    for i in reader:
        print(i)

    print("证明不会修改外部对象")
    print(file_obj.read())

    del reader
