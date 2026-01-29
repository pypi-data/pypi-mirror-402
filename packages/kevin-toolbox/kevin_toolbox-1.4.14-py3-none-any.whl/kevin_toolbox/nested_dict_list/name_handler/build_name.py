import re
from .escape_node import escape_node


def build_name(root_node, method_ls, node_ls, b_escape_node=True):
    """
        根据取值方式 method_ls 和取值时使用的键 node_ls，来构造名字 name
            名字 name 的具体介绍参见函数 parse_name()

        参数：
            root_node:          <str> 变量名
            method_ls:          <list of str> 取值方式，可选值为 :|@
            node_ls:            <list> 取值时使用的键
            b_escape_node:      <boolean> 是否尝试对取值的键名 node 进行转义
                                    默认为 True
        返回：
            name
    """
    assert isinstance(root_node, (str,))
    assert len(method_ls) == len(node_ls)
    if b_escape_node:
        node_ls = [escape_node(node=i, b_reversed=False, times=1) for i in node_ls]

    temp = [root_node]
    for i in zip(method_ls, node_ls):
        temp.extend(i)
    name = "".join(temp)

    return name
