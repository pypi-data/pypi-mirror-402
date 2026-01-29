import re
from .escape_node import escape_node


def parse_name(name, b_de_escape_node=True):
    r"""
        解释名字 name 得到取值方式 method_ls 和取值时使用的键 node_ls

        参数：
            name:               <str> 名字
                                    由 "<变量名>" 加上多组 "<取值方式><键>" 组成。
                                    <变量名>
                                        在实际使用时，比如 get_value()等函数，一般忽略该部分。
                                    <取值方式>
                                        支持以下几种:
                                            "@"     表示使用 eval() 读取键
                                            ":"     表示使用 str() 读取键
                                            "|"     表示依次尝试 str() 和 eval() 两种方式
                                        示例:
                                            "@100"      表示读取 var[eval("100")]
                                            ":epoch"    表示读取 var["epoch"]
                                            "|1+1"    表示首先尝试读取 var["1+1"]，若不成功则尝试读取 var[eval("1+1")]
                                    <键>
                                        对于含有特殊字符 :|@ 的 node，应该先对 node 中的这些特殊字符使用 \ 进行转义
                                            比如，对于：
                                                var={"acc@epoch=1": 0.05, "acc@epoch=2": 0.06}
                                            在 var["acc@epoch=1"] 位置上的元素的名字可以是
                                                "var:acc\@epoch=1"
            b_de_escape_node:  <boolean> 是否尝试对取值的键名 node 进行反转义
                                    默认为 True
        返回：
            root_node, method_ls, node_ls
    """
    assert isinstance(name, (str,))

    temp = re.split(r'(?<!\\)([:@|])', name)
    root_node = temp.pop(0)
    method_ls, node_ls = temp[0::2], temp[1::2]
    if b_de_escape_node:
        node_ls = [escape_node(node=i, b_reversed=True, times=1) for i in node_ls]
    return root_node, method_ls, node_ls
