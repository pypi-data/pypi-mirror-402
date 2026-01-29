from kevin_toolbox.nested_dict_list import set_value, get_value


def eval_references(var, node_s, order, converter_for_ref=None, converter_for_res=None):
    """
        将 var 中的具有引用的值替换为计算结果

        参数：
            var:
            node_s:                 <dict> 引用节点，parse_references() 返回的结果
            order:                  <list of name> 计算顺序，cal_relation_between_references() 返回的结果
            converter_for_ref:      <callable> 对被引用节点施加何种处理
                                        形如 def(idx, v): ... 的函数，其中 idx 是被引用节点的名字，v是其值，
                                        返回的结果将替换掉被引用节点中原来的值。
                                        注意：
                                            - 处理后得到的结果将替换掉原引用节点的值。（重要所以说两次）
                                            - 当同一节点被多次引用时，仅会被处理、替换一次。
            converter_for_res:      <callable> 对计算结果施加何种处理
                                        形如 def(idx, v): ... 的函数，其中 idx 是节点的名字，v是计算结果
    """
    assert order is not None and set(order).issubset(set(node_s.keys()))
    assert converter_for_ref is None or callable(converter_for_ref)
    assert converter_for_res is None or callable(converter_for_res)

    processed_ref_nodes = set()

    for name in order:
        details = node_s[name]
        # 获取依赖值
        for k, idx in details["paras"].items():
            v_new = get_value(var=var, name=idx)
            if converter_for_ref is not None and idx not in processed_ref_nodes:
                v_new = converter_for_ref(idx, v_new)
                # 赋值
                set_value(var=var, name=idx, value=v_new, b_force=False)
                processed_ref_nodes.add(idx)
            details["paras"][k] = v_new
        # 计算
        res = eval(details["expression"], details["paras"])
        if converter_for_res is not None:
            res = converter_for_res(name, res)
        # 赋值
        set_value(var=var, name=name, value=res, b_force=False)

    return var
