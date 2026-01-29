from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.computer_science.algorithm.pareto_front import get_pareto_points_idx, Direction
import kevin_toolbox.nested_dict_list as ndl
import numpy as np


class Optimum_Picker:
    """
        记录并更新帕累托最优值
            同时支持监控以下行为：
                - 新加值是一个新的帕累托最优值
                - 抛弃一个不再是最优的旧的最优值
            并触发设定的执行器，详见参数 trigger_for_new 和 trigger_for_out
    """

    def __init__(self, **kwargs):
        """
            参数：
                directions:             <list of Direction> 比较的方向
                trigger_for_new:        <Executor> 触发器
                                            当 add() 新添加的监控值是一个新的帕累托最优时，执行该触发器
                                            在执行前，将自动往触发器的 kwargs 中添加 {"metrics": <metrics>, "step": <step>, ...} 等信息
                trigger_for_out:        <Executor> 触发器
                                            当 add() 时候需要抛弃一些不再是的帕累托最优的历史值时，执行该触发器
                                            在执行前，将自动往触发器的 kwargs 中添加 {"metrics": <metrics>, "step": <step>, ...} 等信息
                warmup_steps:           <int> 在经过多少次 add() 之后，再开始比较监控值
                                            默认为 0
                pick_per_steps:         <int> 每经过多少次 add()，就比较一次监控值
                                            默认为 1
        """
        # 默认参数
        paras = {
            "directions": None,
            "trigger_for_new": None,
            "trigger_for_out": None,
            "warmup_steps": 0,
            "pick_per_steps": 1,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert paras["warmup_steps"] >= 0 and paras["pick_per_steps"] >= 1
        paras["directions"] = [Direction(i) for i in paras["directions"]]
        for k in ["trigger_for_out", "trigger_for_new"]:
            assert isinstance(paras[k], (type(None), Executor))

        self.paras = paras
        self._state = self._init_state()

    def _init_state(self):
        return dict(
            optimal_ls=list(),  # [{"metrics":metrics, "record":record, "step":step}, ...]
            step=0,
            b_empty_cache=True,
            last_optimal_nums=0
        )

    def add(self, metrics, b_force_clear_cache=False, **kwargs):
        """
            添加指标

            参数：
                metrics:                    指标
                b_force_clear_cache:        <boolean> 是否强制清空缓存
                                                默认为 False，此时将根据设定的 warmup_steps 和 pick_per_steps 来决定何时清空一次缓存
                **kwargs:                   用户自定义记录
                                                将被添加到 record 中
        """
        assert metrics is not None
        metrics = np.asarray(metrics).reshape(1, -1)
        assert metrics.shape[-1] == len(self.paras["directions"])

        optimal_ls, step = self._state["optimal_ls"], self._state["step"]
        new_record = dict(metrics=metrics, step=step)
        new_record.update(kwargs)
        #
        optimal_ls.append(new_record)
        self._state["step"] += 1

        # warmup & cache
        if not b_force_clear_cache and (step < self.paras["warmup_steps"] or
                                        (step - self.paras["warmup_steps"]) % self.paras["pick_per_steps"] != 0):
            self._state["b_empty_cache"] = False
            return

        # 找出新的帕累托最优值
        points = np.concatenate([i["metrics"] for i in optimal_ls])
        idx_ls = get_pareto_points_idx(points=points, directions=self.paras["directions"])
        idx_ls.sort()
        # 进行触发操作
        if self.paras["trigger_for_new"] is not None:
            for i in filter(lambda i: i >= self._state["last_optimal_nums"], idx_ls):
                self.paras["trigger_for_new"].run(**optimal_ls[i])
        #
        if self.paras["trigger_for_out"] is not None:
            for i in set(range(self._state["last_optimal_nums"])).difference(set(idx_ls)):
                self.paras["trigger_for_out"].run(**optimal_ls[i])

        # 更新
        self._state["optimal_ls"] = [optimal_ls[i] for i in idx_ls]
        self._state["b_empty_cache"] = True
        self._state["last_optimal_nums"] = len(idx_ls)

    def get(self, b_force_clear_cache=False):
        """
            获取当前最优值记录

            参数：
                b_force_clear_cache:        <boolean> 是否强制清空缓存

            返回：
                record_ls:          <list of dict> 最优记录
                b_empty_cache:      <boolean> 缓存是否清空，亦即 record_ls 是否是真正的最优记录
                                        当 pick_per_steps > 1 时，将有部分记录留存在缓存中，没有进行比较，此时的最优记录并不是完整的也不是最新的
        """
        if b_force_clear_cache and not self._state["b_empty_cache"] and len(self._state["optimal_ls"]) > 0:
            # 需要清空缓存，就把最后一次缓存的记录拿出来，重新使用 b_force_clear_cache=False 去 add 一次
            record = self._state["optimal_ls"].pop(-1)
            metrics, step = record.pop("metrics"), record.pop("step")
            self._state["step"] -= 1
            assert self._state["step"] == step
            self.add(metrics=metrics, b_force_clear_cache=True, **record)

        return self._state["optimal_ls"][:], self._state["b_empty_cache"] or b_force_clear_cache

    def clear(self):
        self._state = self._init_state()

    def __len__(self):
        return self._state["step"]

    # ---------------------- 用于保存和加载状态 ---------------------- #
    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self._state.update(state_dict)

    def state_dict(self):
        """
            获取状态
        """
        return ndl.copy_(var=self._state, b_deepcopy=True, b_keep_internal_references=True)


if __name__ == '__main__':
    """
        模拟场景
            在训练模型时，要求比较 val_acc_1（maximize） 和 val_error_2（minimize），
            要求保存其帕累托最优时的模型。
    """
    import torch
    import matplotlib.pyplot as plt

    # 一个打乱的圆的采样点序列
    metrics = torch.tensor([(-4.045084971874739, -2.9389262614623632),
                            (-3.1871199487434474, -3.852566213878947),
                            (-2.1288964578253635, 4.524135262330097),
                            (-4.648882429441257, -1.8406227634233896),
                            (-4.648882429441256, 1.8406227634233907),
                            (-0.936906572928623, 4.911436253643443),
                            (0.31395259764656414, -4.990133642141358),
                            (-4.960573506572389, 0.6266661678215226),
                            (-3.1871199487434487, 3.852566213878946),
                            (4.381533400219316, -2.4087683705085805),
                            (0.31395259764656763, 4.990133642141358),
                            (2.6791339748949827, 4.221639627510076),
                            (4.8429158056431545, -1.2434494358242767),
                            (1.5450849718747361, -4.755282581475768),
                            (4.842915805643155, 1.243449435824274),
                            (3.644843137107056, -3.422735529643445),
                            (5.0, 0.0),
                            (-2.128896457825361, -4.524135262330099),
                            (2.6791339748949836, -4.221639627510075),
                            (-4.9605735065723895, -0.6266661678215214),
                            (3.644843137107058, 3.422735529643443),
                            (4.381533400219318, 2.4087683705085765),
                            (-0.9369065729286231, -4.911436253643443),
                            (-4.045084971874736, 2.9389262614623664),
                            (1.5450849718747373, 4.755282581475767)])
    # 右下角的点是帕累托最优
    best_idx_ls = [6, 9, 12, 13, 15, 16, 18]

    # 将x和y坐标分别存储在两个列表中
    x_coords = metrics[:, 0].numpy().tolist()
    y_coords = metrics[:, 1].numpy().tolist()
    # 按顺序绘制点
    plt.plot(x_coords, y_coords, marker='o')
    # 添加顺序标签
    for i, txt in enumerate(range(len(metrics))):
        plt.annotate(txt, (x_coords[i], y_coords[i]), textcoords="offset points", xytext=(0, 5), ha='center')
    plt.show()
    import os
    from kevin_toolbox.data_flow.file import json_
    from kevin_toolbox.patches.for_os import remove

    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    remove(temp_dir, ignore_errors=True)

    opt_picker = Optimum_Picker(
        warmup_steps=9, pick_per_steps=5,
        trigger_for_new=Executor(
            func=lambda metrics, step: json_.write(metrics.tolist(), os.path.join(temp_dir, f'{step}.json'))),
        trigger_for_out=Executor(func=lambda step, **kwargs: remove(os.path.join(temp_dir, f'{step}.json'))),
        directions=["maximize", "minimize"]
    )
    for s, v in enumerate(metrics):
        opt_picker.add(metrics=v)
        print()
        print(s, v)
        print(opt_picker.get()[1])
        print([i["step"] for i in opt_picker.get()[0]])

    for i in best_idx_ls:
        assert os.path.isfile(os.path.join(temp_dir, f'{i}.json'))
