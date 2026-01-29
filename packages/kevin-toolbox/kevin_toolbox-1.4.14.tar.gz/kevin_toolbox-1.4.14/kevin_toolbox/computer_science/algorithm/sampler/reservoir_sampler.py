from kevin_toolbox.computer_science.algorithm.sampler import analog_resample
from kevin_toolbox.patches.for_numpy.random import get_rng, get_rng_state, set_rng_state


class Reservoir_Sampler:
    def __init__(self, **kwargs):
        """
            水库采样

            参数：
                target_nums:            <int> 采样数量
                b_allow_duplicates:     <boolean> 是否允许重复采样。
                                            默认为 False
                b_keep_order:           <boolean> 返回的样本序列是否需要保持历史先后顺序。
                                            默认为 False
                    （注意：当 b_allow_duplicates 设置为 True 时， b_keep_order 无效。）
                seed, rng:                      设定随机发生器
        """
        # 默认参数
        paras = {
            "target_nums": 1,
            "b_allow_duplicates": False,
            "b_keep_order": False,
            #
            "seed": None,
            "rng": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(paras["target_nums"], (int,)) and paras["target_nums"] >= 0

        self.paras = paras

        self.samples = []
        self.state = self._init_state()
        self.rng = get_rng(seed=paras["seed"], rng=paras["rng"])

    @staticmethod
    def _init_state():
        """
            初始化状态
        """
        return dict(
            total_nums=0,
        )

    def add(self, item, **kwargs):
        if len(self.samples) < self.paras["target_nums"]:
            # 对于前 target_nums 个 item，全部保留
            self.samples.append(item)
        else:
            # 对于之后的 item，我们以 target_nums/total_nums+1 的概率保留第i个数，
            # 并替换掉 samples 中的随机一个 item。
            idx = self.rng.randint(0, self.state["total_nums"])
            if idx < self.paras["target_nums"]:
                if self.paras["b_keep_order"]:
                    self.samples.pop(idx)
                    self.samples.append(item)
                else:
                    self.samples[idx] = item
        self.state["total_nums"] += 1

    def add_sequence(self, item_ls, **kwargs):
        for item in item_ls:
            self.add(item, **kwargs)

    def get(self, **kwargs):
        res = self.samples
        if self.paras["b_allow_duplicates"]:
            res = analog_resample(samples=res, total_nums=self.state["total_nums"], rng=self.rng)

        return res

    def clear(self):
        self.samples.clear()
        self.state = self._init_state()
        self.rng = get_rng(seed=self.paras["seed"], rng=self.paras["rng"])

    def __len__(self):
        return self.state["total_nums"]

    # ---------------------- 用于保存和加载状态 ---------------------- #

    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.state.update(state_dict["state"])
        self.samples.extend(state_dict["samples"])
        set_rng_state(state=state_dict["rng_state"], rng=self.rng)

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"state": self.state, "samples": self.samples, "rng_state": get_rng_state(rng=self.rng)}
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp


if __name__ == "__main__":
    sampler = Reservoir_Sampler(target_nums=5, seed=12345, b_keep_order=False)
    for i in range(1, 21):
        sampler.add(i)
    print("当前水库数据:", sampler.get())

    state = sampler.state_dict()
    print("状态字典:", state)

    # 清空后再恢复状态
    sampler.clear()
    print("清空后:", sampler.get())

    sampler.load_state_dict(state)
    print("恢复后水库数据:", sampler.get())
