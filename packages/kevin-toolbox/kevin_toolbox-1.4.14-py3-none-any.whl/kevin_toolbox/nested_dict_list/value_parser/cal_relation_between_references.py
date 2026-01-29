from kevin_toolbox.nested_dict_list.name_handler import parse_name
from kevin_toolbox.nested_dict_list import copy_


def cal_relation_between_references(node_s, b_verbose=False):
    """
        计算具有引用的节点之间的关系
            当节点之间的依赖关系满足有向无环图 DAG 时，会输出便于计算节点的顺序 order

        参数：
            node_s:             <dict> parse_references() 返回的结果

        返回：
            node_s, b_is_DAG, order

            node_s:             <dict> 在输入的 node_s 的基础上为每个节点补充 upstream_node 和 downstream_node 字段
                                    其中：
                                        upstream_node 中保存该节点所依赖的上游节点，意味着要等这些上游节点计算完毕后才能计算该节点
                                        downstream_node 中保存对该节点有依赖的下游节点。
            b_is_DAG:           <boolean> 节点关系是否满足有向无环图 DAG
            order:              <list of name> 节点在 DAG 中的顺序
    """

    for v in node_s.values():
        v.update(dict(upstream_node=set(), downstream_node=set()))

    for name_i, details_i in node_s.items():
        for name_j, details_j in node_s.items():
            #
            for ref_name in details_i["paras"].values():
                _, method_ls_r, node_ls_r = parse_name(name=ref_name, b_de_escape_node=False)
                _, method_ls_j, node_ls_j = parse_name(name=name_j, b_de_escape_node=False)
                len_ = min(len(method_ls_r), len(method_ls_j))
                if method_ls_r[:len_] == method_ls_j[:len_] and node_ls_r[:len_] == node_ls_j[:len_]:
                    details_i["upstream_node"].add(name_j)
                    details_j["downstream_node"].add(name_i)
                    break

    # 按照上下游依赖关系进行排序
    upstream_node_names = set()
    downstream_node_s = copy_(var=node_s, b_deepcopy=True)
    order = []
    while True:
        # 将已解释节点放入 order
        order += list(upstream_node_names)
        upstream_node_names.clear()
        # 找出下游节点中已经无依赖的节点，作为新的已解释节点
        for ref_name, details in list(downstream_node_s.items()):
            if len(details["upstream_node"]) == 0:
                upstream_node_names.add(ref_name)
                downstream_node_s.pop(ref_name)
        if len(upstream_node_names) == 0:
            break
        # 清除下游节点中对已解释节点（放置在upstream_node_names中）的依赖
        for details in downstream_node_s.values():
            details["upstream_node"].difference_update(upstream_node_names)
    #
    b_is_DAG = len(downstream_node_s) == 0
    if not b_is_DAG:
        order = None
        if b_verbose:
            print(f'There is a loop in the dependency relationship, and the parsing fails. \n'
                  f'Please check the relationship between the following nodes: {list(downstream_node_s.keys())}')

    return node_s, b_is_DAG, order
