class Node:
    def __init__(self, **kwargs):
        """
            设定关键参数

            参数：
                file_path:  文件路径
            读取模式相关参数：
                paras_for_open:     open() 函数的补充参数
                mode:       读取模式，默认为 "lines"
                                "lines"：  按行数计算批次大小
                                "bytes"：  按字节数计算
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
                map_func:   后处理函数。
                                对读取的 "lines" 或者 "bytes" 进行什么处理。
                                默认使用strip()去除首、尾的空格、换行符。
                处理流程： ==> filter_ ==> drop ==> map_func ==>
            返回：
                类型取决于 mode（"lines"返回的是列表，"bytes"是单个字符串） 以及 map_func 的处理结果
        """

        # 默认参数
        paras = {
            #
            "uid": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert paras["uid"] in ["lines", "bytes"]
        paras["chunk_size"] = int(paras["chunk_size"])
