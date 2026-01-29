import kevin_toolbox.nested_dict_list as ndl
from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.computer_science.algorithm.for_dict import deep_update
from kevin_toolbox.data_flow.file import markdown


class Jump_Node:
    """
        在执行图上进行跳转
            只能设置单个上游/下游节点
    """

    def __init__(self, name, predecessor, successor,target, **kwargs):
        assert callable(pipeline)

        self.name = name
        self.pipeline = None
        # 对于 relation_s，其中 predecessor 字段下保存有：
        #   {<predecessor_node>: [(<output_name>, <input_name>), ...], ...}
        #   其中：
        #       - <predecessor_node>： 前继节点名
        #       - <output_name>： 从该前继节点输出的结果中取出对应部分
        #       - <input_name>： 将取出的部分填入到本节点的 self.paras 中对应位置上
        # 对于 successor字段，其中保存后继节点的名字
        self.relation_s = {
            "predecessor": dict(),
            "successor": set(),
        }
        self.relation_s = deep_update(stem=self.relation_s,
                                      patch={k: kwargs[k] for k in self.relation_s.keys() if k in kwargs})
        self.paras = {
            "args": list(),
            "f_args": list(),
            "kwargs": dict(),
            "f_kwargs": dict(),
        }
        self.paras = deep_update(stem=self.paras,
                                 patch={k: kwargs[k] for k in self.paras.keys() if k in kwargs})
        self.parse()

    def parse(self):
        def func(idx, value):
            nonlocal self
            predecessor, output_name = value.split("{", 1)[-1].split("}", 1)
            if predecessor not in self.relation_s["predecessor"]:
                self.relation_s["predecessor"][predecessor] = []
            self.relation_s["predecessor"][predecessor].append((output_name, idx))
            return None

        ndl.traverse(
            var=self.paras, match_cond=lambda _, __, value: isinstance(value, (str,)) and value.startswith("<exe>"),
            action_mode="replace", converter=func, b_use_name_as_idx=True
        )

    def run(self, predecessor_output_s):
        for k, v in predecessor_output_s.items():
            for output_name, input_name in self.relation_s["predecessor"][k]:
                ndl.set_value(var=self.paras, name=input_name, value=ndl.get_value(var=v, name=output_name),
                              b_force=True)
        if len(self.paras["f_args"]) == len(self.paras["f_kwargs"]) == 0:
            res = self.pipeline(*self.paras["args"], **self.paras["kwargs"])
        else:
            res = Executor(func=self.pipeline, **self.paras).run()
        return res

    def __repr__(self):
        doc = f'<Simple_Node> with name: {self.name}\n' \
              f'\tpipeline: {self.pipeline}\n' \
              f'\tparas: \n'
        doc += markdown.generate_list(var=self.paras, indent=8)
        doc += f'\trelation_s: \n'
        doc += markdown.generate_list(var=self.relation_s, indent=8)
        return doc


if __name__ == '__main__':
    node = Simple_Node(name="@0", pipeline=lambda x, y: x + y, args=["<exe>{@1}:x"], f_kwargs={"y": "<exe>{@2}"})
    print(node)
