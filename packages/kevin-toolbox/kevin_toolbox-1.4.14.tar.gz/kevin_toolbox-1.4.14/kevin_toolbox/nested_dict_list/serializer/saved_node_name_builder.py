class Saved_Node_Name_Builder:
    """
        生成保存节点内容时的文件夹/文件名称
    """

    def __init__(self, format_):
        try:
            temp = format_.format(**{k: k + "_" * 3 for k in {"raw_name", "id", "hash_name", "count"}})
            assert len(temp) > len(format_)
        except:
            raise ValueError(f'invalid saved_node_name_format {format_}')

        self.format_ = format_
        self.count = 0

    def __call__(self, name, value):
        from kevin_toolbox.nested_dict_list import get_hash

        res = self.format_.format(
            **{"raw_name": name, "id": id(value), "hash_name": get_hash(name, length=12), "count": self.count})
        self.count += 1
        return res


if __name__ == '__main__':
    bd = Saved_Node_Name_Builder(format_="{raw_name}_{count}_{hash_name}_{id}")
    print(bd(":a@0", 1))
    print(bd(":b:c", []))

    # bd = Saved_Node_Name_Builder(format_="")
    # bd = Saved_Node_Name_Builder(format_="{raw_name2}_{count}")
